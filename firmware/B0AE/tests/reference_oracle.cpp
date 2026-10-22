
#include <stdio.h>
#include <math.h>
typedef unsigned char u8;typedef unsigned short u16;typedef signed char s8;
typedef short s16;typedef int s32;typedef unsigned int u32;
#define X 0
#define Y 1
#define Z 2
#define KP 0
#define KI 1
#define KD 2
#define CH_PIT 1
#define CH_ROL 0
#define CH_THR 2
#define CH_YAW 3
#define MAX_Z_SPEED_UP 350
#define MAX_Z_SPEED_DW 250
#define MAX_SPEED 500
#define MAX_ANGLE 25.f
#define FINAL_P .35f
#define THR_INTE_LIM (70/FINAL_P)
#define THR_START 35
#define MAX_THR_SET 85
#define THR_AUTO 1
#define AUTO_TAKE_OFF_NULL 0
#define AUTO_TAKE_OFF 1
#define AUTO_TAKE_OFF_FINISH 2
#define AUTO_LAND 3
#define ROLL_END 0
#define LIMIT(a,l,h) ((a)<(l)?(l):((a)>(h)?(h):(a)))
#define ABS(a) ((a)>0?(a):-(a))
#define my_pow(a) ((a)*(a))
#define my_2_norm(x,y) (my_sqrt(my_pow(x)+my_pow(y)))
#define LPF_1_(hz,t,in,out) ((out)+=(1/(1+1/((hz)*6.28f*(t))))*((in)-(out)))
#define MOTORSNUM 4
#define m1 0
#define m2 1
#define m3 2
#define m4 3
struct {u8 unlock_sta,unlock_cmd,motor_preparation,taking_off,flying,thr_low,locking,
 wifi_ch_en,auto_take_off_land,ct_alt_hold,thr_mode,sensor_imu_ok,rc_loss_back_home,flight_mode;} flag;
struct {float vel_limit_z_p,vel_limit_z_n,vel_limit_xy;} fc_stv;
struct {s16 alt_ctrl_speed_set;float speed_set_h[3],speed_set_h_cms[3],speed_set_h_norm[3],speed_set_h_norm_lpf[3];} fs;
struct {float out;} wcz_hei_fus,wcz_spe_fus;
struct {float exp[3],fb[3],out[3];} loc_ctrl_1,loc_ctrl_2;
struct {float vel_cmps_h[3];} program_ctrl;
struct {float vel_cmps_set_z,vel_cmps_set_h[3];} pc_user;
struct {u8 of_flow_on,gps_on;} switchs;
struct {float w_acc[3],h_acc[3],z_vec[3];} imu_data;
struct {u8 G_reset;} imu_state;
struct {u8 gyr_CALIBRATE,acc_CALIBRATE,acc_z_auto_CALIBRATE;} sensor;
struct {u8 mag_CALIBRATE;} mag;
struct {u8 rolling_step;} rolling_flag;
struct {u8 rst_imu;} LED_STA;
struct {float ct_val_thr,ct_val_yaw,ct_val_rol,ct_val_pit;} mc;
struct {struct {float pid_alt_1level[3],pid_alt_2level[3],pid_loc_1level[3];s16 auto_take_off_height,auto_take_off_speed,auto_landing_speed,idle_speed_pwm;} set;} Ano_Parame;
typedef struct {u8 fb_d_mode;float kp,ki,kd_ex,kd_fb,k_ff;} _PID_arg_st;
typedef struct {float err,exp_old,feedback_old,fb_d,fb_d_ex,exp_d,err_i,ff,pre_d,out;} _PID_val_st;
float safe_div(float a,float b,float c){return b!=0?a/b:c;}
void WCZ_Data_Reset(void){}
void ANO_DT_SendString(const char*s){}
void one_key_take_off_task(u16 dt){}
void Drv_MotorPWMSet(u8 a,s16 b){}
s16 CH_N[8],flying_cnt,landing_cnt;
static s16 ld_delay_cnt;

float my_sqrt_reciprocal(float number)
{











	
	long i;
	float x, y;

	x = number * 0.5F;
	y = number;
	i = * ( long * ) &y;
	i = 0x5f3759df - ( i >> 1 );

	y = * ( float * ) &i;
	y = y * ( 1.5f - ( x * y * y ) );
	y = y * ( 1.5f - ( x * y * y ) );
	
	return y;
}
float my_sqrt(float number)
{











	return number * my_sqrt_reciprocal(number);
}
float my_deadzone(float x,float ref,float zoom)
{
	float t;
	if(x>ref)
	{
		t = x - zoom;
		if(t<ref)
		{
			t = ref;
		}
	}
	else
	{
		t = x + zoom;
		if(t>ref)
		{
			t = ref;
		}
	}
  return (t);
}
void length_limit(float *in1,float *in2,float limit,float out[2])
{
	float l = my_2_norm(*in1,*in2);
	float l_lim = LIMIT(l,0,limit);
	
	if(l==0)
	{
		out[0] = out[1] = 0;
	}
	else
	{
		out[0] = l_lim/l *(*in1);
		out[1] = l_lim/l *(*in2);
	}
}
float PID_calculate( float dT_s,            
										float in_ff,				
										float expect,				
										float feedback,			
										_PID_arg_st *pid_arg, 
										_PID_val_st *pid_val,	
										float inte_d_lim,
										float inte_lim			
										 )	
{
	float differential,hz;
	hz = safe_div(1.0f,dT_s,0);
	

	

	
	pid_val->exp_d = (expect - pid_val->exp_old) *hz;
	
	if(pid_arg->fb_d_mode == 0)
	{
		pid_val->fb_d = (feedback - pid_val->feedback_old) *hz;
	}
	else
	{
		pid_val->fb_d = pid_val->fb_d_ex;
	}	
	differential = (pid_arg->kd_ex *pid_val->exp_d - pid_arg->kd_fb *pid_val->fb_d);
	
	pid_val->err = (expect - feedback);	

	pid_val->err_i += pid_arg->ki *LIMIT((pid_val->err ),-inte_d_lim,inte_d_lim )*dT_s;
	
	pid_val->err_i = LIMIT(pid_val->err_i,-inte_lim,inte_lim);
	
	
	
	pid_val->out = pid_arg->k_ff *in_ff 
	    + pid_arg->kp *pid_val->err  
			+	differential

    	+ pid_val->err_i;
	
	pid_val->feedback_old = feedback;
	pid_val->exp_old = expect;
	
	return (pid_val->out);
}
void land_discriminat(s16 dT_ms)
{

	


	
	
	if((fs.speed_set_h_norm[Z] < 0.1f) || flag.auto_take_off_land == AUTO_LAND)
	{
		if(ld_delay_cnt>0)
		{
			ld_delay_cnt -= dT_ms;
		}
	}
	else
	{
		ld_delay_cnt = 200;
	}
	
		
	if(ld_delay_cnt <= 0 && (flag.thr_low || flag.auto_take_off_land == AUTO_LAND) )
	{
		
		if(mc.ct_val_thr<250 && flag.unlock_sta == 1 && flag.locking != 2)
		{
			if(landing_cnt<1500)
			{
				landing_cnt += dT_ms;
			}
			else
			{

				flying_cnt = 0;
				flag.taking_off = 0;
				
					landing_cnt =0;	
					flag.unlock_cmd =0;				

				flag.flying = 0;

			}
		}
		else
		{
			landing_cnt = 0;
		}
			
		
	}
	else
	{
		landing_cnt  = 0;
	}

}
void Flight_State_Task(u8 dT_ms,s16 *CH_N)
{
	s16 thr_deadzone;
	static float max_speed_lim,vel_z_tmp[2];
	
	thr_deadzone = (flag.wifi_ch_en != 0) ? 0 : 50;
	fs.speed_set_h_norm[Z] = my_deadzone(CH_N[CH_THR],0,thr_deadzone) *0.0023f;
	fs.speed_set_h_norm_lpf[Z] += 0.5f *(fs.speed_set_h_norm[Z] - fs.speed_set_h_norm_lpf[Z]);
	
	
	if(flag.unlock_sta)
	{	
		if(fs.speed_set_h_norm[Z]>0.01f && flag.motor_preparation == 1) 
		{
			flag.taking_off = 1;
		}	
	}		
	
	fc_stv.vel_limit_z_p = MAX_Z_SPEED_UP;
	fc_stv.vel_limit_z_n = -MAX_Z_SPEED_DW;	
	
	if( flag.taking_off )
	{
			
		if(flying_cnt<1000)
		{
			flying_cnt += dT_ms;
		}
		else
		{
			
			flag.flying = 1;  
		}
		
		if(fs.speed_set_h_norm[Z]>0)
		{
			
			vel_z_tmp[0] = (fs.speed_set_h_norm_lpf[Z] *MAX_Z_SPEED_UP);
		}
		else
		{
			
			vel_z_tmp[0] = (fs.speed_set_h_norm_lpf[Z] *MAX_Z_SPEED_DW);
		}

		
		vel_z_tmp[1] = vel_z_tmp[0] + program_ctrl.vel_cmps_h[Z] + pc_user.vel_cmps_set_z;
		
		vel_z_tmp[1] = LIMIT(vel_z_tmp[1],fc_stv.vel_limit_z_n,fc_stv.vel_limit_z_p);
		
		fs.speed_set_h[Z] += LIMIT((vel_z_tmp[1] - fs.speed_set_h[Z]),-0.8f,0.8f);
	}
	else
	{
		fs.speed_set_h[Z] = 0 ;
	}
	float speed_set_tmp[2];
	
	fs.speed_set_h_norm[X] = (my_deadzone(+CH_N[CH_PIT],0,50) *0.0022f);
	fs.speed_set_h_norm[Y] = (my_deadzone(-CH_N[CH_ROL],0,50) *0.0022f);
		
	LPF_1_(3.0f,dT_ms*1e-3f,fs.speed_set_h_norm[X],fs.speed_set_h_norm_lpf[X]);
	LPF_1_(3.0f,dT_ms*1e-3f,fs.speed_set_h_norm[Y],fs.speed_set_h_norm_lpf[Y]);
	
	max_speed_lim = MAX_SPEED;
	
	if(switchs.of_flow_on && !switchs.gps_on )
	{
		max_speed_lim = 1.5f *wcz_hei_fus.out;
		max_speed_lim = LIMIT(max_speed_lim,50,150);
	}	
	
	fc_stv.vel_limit_xy = max_speed_lim;
	
	
	speed_set_tmp[X] = fc_stv.vel_limit_xy *fs.speed_set_h_norm_lpf[X] + program_ctrl.vel_cmps_h[X] + pc_user.vel_cmps_set_h[X];
	speed_set_tmp[Y] = fc_stv.vel_limit_xy *fs.speed_set_h_norm_lpf[Y] + program_ctrl.vel_cmps_h[Y] + pc_user.vel_cmps_set_h[Y];
	
	length_limit(&speed_set_tmp[X],&speed_set_tmp[Y],fc_stv.vel_limit_xy,fs.speed_set_h_cms);

	fs.speed_set_h[X] = fs.speed_set_h_cms[X];
	fs.speed_set_h[Y] = fs.speed_set_h_cms[Y];	
	
	
	land_discriminat(dT_ms);
	
	
	if(rolling_flag.rolling_step == ROLL_END)
	{
		if(imu_data.z_vec[Z]<0.25f)
		{
			
			if(mag.mag_CALIBRATE==0)
			{
				imu_state.G_reset = 1;
			}
			flag.unlock_cmd = 0;
		}

	}	
		
	
	if(sensor.gyr_CALIBRATE != 0 || sensor.acc_CALIBRATE != 0 ||sensor.acc_z_auto_CALIBRATE)
	{
		imu_state.G_reset = 1;
	}
	
	
	if(imu_state.G_reset == 1)
	{
		flag.sensor_imu_ok = 0;
		LED_STA.rst_imu = 1;
		WCZ_Data_Reset(); 
	}
	else if(imu_state.G_reset == 0)
	{	
		if(flag.sensor_imu_ok == 0)
		{
			flag.sensor_imu_ok = 1;
			LED_STA.rst_imu = 0;
			ANO_DT_SendString("IMU OK!");
		}
	}
	
	
	if(flag.unlock_sta == 0)
	{
		flag.flying = 0;
		landing_cnt = 0;
		flag.taking_off = 0;
		flying_cnt = 0;
		
		
		flag.rc_loss_back_home = 0;
		
		
		if(flag.taking_off == 0)
		{

		}
	}
	

}












static s16 auto_taking_off_speed;

#define AUTO_TAKE_OFF_KP 2.0f

void Auto_Take_Off_Land_Task(u8 dT_ms)
{
	static u16 take_off_ok_cnt;
	
	one_key_take_off_task(dT_ms);
	
	if(flag.unlock_sta)
	{
		if(flag.taking_off)
		{	
			if(flag.auto_take_off_land == AUTO_TAKE_OFF_NULL)
			{
				flag.auto_take_off_land = AUTO_TAKE_OFF;		
			}
		}

	}
	else
	{
		auto_taking_off_speed = 0;	
		flag.auto_take_off_land = AUTO_TAKE_OFF_NULL;	
	}

	
	if(flag.auto_take_off_land ==AUTO_TAKE_OFF)
	{
		
		s16 max_take_off_vel = LIMIT(Ano_Parame.set.auto_take_off_speed,20,200);
		
		take_off_ok_cnt += dT_ms;
		auto_taking_off_speed = AUTO_TAKE_OFF_KP *(Ano_Parame.set.auto_take_off_height - wcz_hei_fus.out);
		
		auto_taking_off_speed = LIMIT(auto_taking_off_speed,0,max_take_off_vel);
		
		
		if(take_off_ok_cnt>=5000 || (Ano_Parame.set.auto_take_off_height - loc_ctrl_2.exp[Z] <2))
		{
			flag.auto_take_off_land = AUTO_TAKE_OFF_FINISH;
			
			
		}
		
		if(take_off_ok_cnt >2000 && ABS(fs.speed_set_h_norm[Z])>0.1f)
		{
			flag.auto_take_off_land = AUTO_TAKE_OFF_FINISH;
		}
	
	}
	else 
	{
		take_off_ok_cnt = 0;
		
		if(flag.auto_take_off_land ==AUTO_TAKE_OFF_FINISH)
		{
			auto_taking_off_speed = 0;
			
		}
		
	}



	
	if(flag.auto_take_off_land == AUTO_LAND)
	{
		
		auto_taking_off_speed = -(s16)LIMIT(Ano_Parame.set.auto_landing_speed,20,200);

	}
}


_PID_arg_st alt_arg_2;
_PID_val_st alt_val_2;


void Alt_2level_PID_Init()
{
	alt_arg_2.kp = Ano_Parame.set.pid_alt_2level[KP];
	alt_arg_2.ki = Ano_Parame.set.pid_alt_2level[KI];
	alt_arg_2.kd_ex = 0.00f;
	alt_arg_2.kd_fb = Ano_Parame.set.pid_alt_2level[KD];
	alt_arg_2.k_ff = 0.0f;

}




void Alt_2level_Ctrl(float dT_s)
{
	Auto_Take_Off_Land_Task(1000*dT_s);
	
	fs.alt_ctrl_speed_set = fs.speed_set_h[Z] + auto_taking_off_speed;
	
	loc_ctrl_2.exp[Z] += fs.alt_ctrl_speed_set *dT_s;
	loc_ctrl_2.exp[Z] = LIMIT(loc_ctrl_2.exp[Z],loc_ctrl_2.fb[Z]-200,loc_ctrl_2.fb[Z]+200);
	
	loc_ctrl_2.fb[Z] = (s32)wcz_hei_fus.out;
	
	if(fs.alt_ctrl_speed_set != 0)
	{
		flag.ct_alt_hold = 0;
	}
	else
	{
		if(ABS(loc_ctrl_1.exp[Z] - loc_ctrl_1.fb[Z])<20)
		{
			flag.ct_alt_hold = 1;
		}
	}

	if(flag.taking_off == 1)
	{

		PID_calculate( dT_s,            
						0,				
						loc_ctrl_2.exp[Z],				
						loc_ctrl_2.fb[Z],			
						&alt_arg_2, 
						&alt_val_2,	
						100,
						0			
						 );

	}
	else
	{
		loc_ctrl_2.exp[Z] = loc_ctrl_2.fb[Z];
		alt_val_2.out = 0;
		
	}
	
	alt_val_2.out  = LIMIT(alt_val_2.out,-150,150);
}



_PID_arg_st alt_arg_1;
_PID_val_st alt_val_1;


void Alt_1level_PID_Init()
{
	alt_arg_1.kp = Ano_Parame.set.pid_alt_1level[KP];
	alt_arg_1.ki = Ano_Parame.set.pid_alt_1level[KI];
	alt_arg_1.kd_ex = 0.00f;
	alt_arg_1.kd_fb = 0;
	alt_arg_1.k_ff = 0.0f;

}


static float err_i_comp;
static float w_acc_z_lpf;
void Alt_1level_Ctrl(float dT_s)
{
	u8 out_en;
	out_en = (flag.taking_off != 0) ? 1 : 0;
	
	flag.thr_mode = THR_AUTO;
	
	loc_ctrl_1.exp[Z] = 0.6f *fs.alt_ctrl_speed_set + alt_val_2.out;
	
	w_acc_z_lpf += 0.2f *(imu_data.w_acc[Z] - w_acc_z_lpf); 

	loc_ctrl_1.fb[Z] = wcz_spe_fus.out + Ano_Parame.set.pid_alt_1level[KD] *w_acc_z_lpf;
	
	
	PID_calculate( dT_s,            
					0,				
					loc_ctrl_1.exp[Z],				
					loc_ctrl_1.fb[Z] ,			
					&alt_arg_1, 
					&alt_val_1,	
					100,
					(THR_INTE_LIM *10 - err_i_comp )*out_en			
					 );
	
	if(flag.taking_off == 1)
	{
		LPF_1_(1.0f,dT_s,THR_START *10,err_i_comp);
	}
	else
	{
		err_i_comp = 0;
	}
	

	
	loc_ctrl_1.out[Z] = out_en *(alt_val_1.out + err_i_comp);
	
	loc_ctrl_1.out[Z] = LIMIT(loc_ctrl_1.out[Z],0,MAX_THR_SET *10);	
	
	mc.ct_val_thr = loc_ctrl_1.out[Z];
}


s16 motor[MOTORSNUM];
s16 motor_step[MOTORSNUM];
//float motor_lpf[MOTORSNUM];

static u16 motor_prepara_cnt;

u16 IDLING;//10*Ano_Parame.set.idle_speed_pwm  //200

void Motor_Ctrl_Task(u8 dT_ms)
{
	u8 i;
	





	
	if(flag.unlock_sta)
	{		
		IDLING = 10*LIMIT(Ano_Parame.set.idle_speed_pwm,0,30);
		
		if(flag.motor_preparation == 0)
		{
			motor_prepara_cnt += dT_ms;
			
			if(flag.motor_preparation == 0)
			{			
				if(motor_prepara_cnt<300)
				{
					motor[m1] = IDLING;
				}
				else if(motor_prepara_cnt<600)
				{
					motor[m2] = IDLING;
				}
				else if(motor_prepara_cnt<900)
				{
					motor[m3] = IDLING;
				}	
				else if(motor_prepara_cnt<1200)
				{	
					motor[m4] = IDLING;
				}
				else
				{
					flag.motor_preparation = 1;
					motor_prepara_cnt = 0;
				}
			}
			
		}	
	}
	else
	{
		flag.motor_preparation = 0;
	}
	

			
	if(flag.motor_preparation == 1)
	{	
		motor_step[m1] = mc.ct_val_thr  +mc.ct_val_yaw -mc.ct_val_rol +mc.ct_val_pit;
		motor_step[m2] = mc.ct_val_thr  -mc.ct_val_yaw +mc.ct_val_rol +mc.ct_val_pit;
		motor_step[m3] = mc.ct_val_thr  +mc.ct_val_yaw +mc.ct_val_rol -mc.ct_val_pit;
		motor_step[m4] = mc.ct_val_thr  -mc.ct_val_yaw -mc.ct_val_rol -mc.ct_val_pit;
		
	
		for(i=0;i<MOTORSNUM;i++)
		{	
			motor_step[i] = LIMIT(motor_step[i],IDLING,1000);

			
		}
		


	}
	
	for(i=0;i<MOTORSNUM;i++)
	{
		if(flag.unlock_sta)
		{
			if(flag.motor_preparation == 1)
			{
				motor[i] = LIMIT(motor_step[i],IDLING,999);
			}
	
		}
		else
		{		
			motor[i] = 0;
		}	

	}

	
	for(u8 i =0;i<4;i++)
	{
		Drv_MotorPWMSet(i,motor[i]);
	}


#ifdef Cali_Set_ESC
	
	for(u8 i =0;i<4;i++)
	{
		motor[i] = CH_N[CH_THR]+500;
		Drv_MotorPWMSet(i,motor[i]);
	}
	
#endif
	


}
_PID_arg_st loc_arg_1[2],loc_arg_1_fix[2];
_PID_val_st loc_val_1[2],loc_val_1_fix[2];
static u8 mode_f[2];
float vel_fb_d_lpf[2],fb_speed_fix[2];
struct {u8 of_ok;} sens_hd_check;
struct {float gnd_vel_est_h[3];} of_rdf;
#define OF_DX2 of_rdf.gnd_vel_est_h[0]
#define OF_DY2 of_rdf.gnd_vel_est_h[1]
#define OF_DX2FIX of_rdf.gnd_vel_est_h[0]
#define OF_DY2FIX of_rdf.gnd_vel_est_h[1]
void Loc_1level_PID_Init(){
		
		loc_arg_1[X].kp = Ano_Parame.set.pid_loc_1level[KP];
		loc_arg_1[X].ki = 0.0f  ;
		loc_arg_1[X].kd_ex = 0.00f ;
		loc_arg_1[X].kd_fb = Ano_Parame.set.pid_loc_1level[KD];
		loc_arg_1[X].k_ff = 0.02f;
		
		loc_arg_1[Y] = loc_arg_1[X];
		
		loc_arg_1_fix[X].kp = 0.0f  ;
		loc_arg_1_fix[X].ki = Ano_Parame.set.pid_loc_1level[KI] ;
		loc_arg_1_fix[X].kd_ex = 0.00f;
		loc_arg_1_fix[X].kd_fb = 0.00f;
		loc_arg_1_fix[X].k_ff = 0.0f;
		
		loc_arg_1_fix[Y] = loc_arg_1_fix[X];	
	}
void Loc_OF_Reference(u16 dT_ms){
		mode_f[1] = 1;
		if(mode_f[1] != mode_f[0])
		{
			Loc_1level_PID_Init();
			mode_f[0] = mode_f[1];
		}
		
		loc_ctrl_1.exp[X] = fs.speed_set_h[X];
		loc_ctrl_1.exp[Y] = fs.speed_set_h[Y];
		
		LPF_1_(5.0f,dT_ms*1e-3f,imu_data.h_acc[X],vel_fb_d_lpf[X]);
		LPF_1_(5.0f,dT_ms*1e-3f,imu_data.h_acc[Y],vel_fb_d_lpf[Y]);		
		
		if(sens_hd_check.of_ok)
		{
			loc_ctrl_1.fb[X] = OF_DX2 + 0.03f *vel_fb_d_lpf[X];
			loc_ctrl_1.fb[Y] = OF_DY2 + 0.03f *vel_fb_d_lpf[Y];
			
			fb_speed_fix[0] = OF_DX2FIX;
			fb_speed_fix[1] = OF_DY2FIX;
		}
		else
		{
			loc_ctrl_1.fb[X] = of_rdf.gnd_vel_est_h[X] + 0.03f *vel_fb_d_lpf[X];
			loc_ctrl_1.fb[Y] = of_rdf.gnd_vel_est_h[Y] + 0.03f *vel_fb_d_lpf[Y];
			
			fb_speed_fix[0] = of_rdf.gnd_vel_est_h[X];
			fb_speed_fix[1] = of_rdf.gnd_vel_est_h[Y];		
		}
		
		for(u8 i =0;i<2;i++)
		{
			PID_calculate( dT_ms*1e-3f,            
										loc_ctrl_1.exp[i] ,				
										loc_ctrl_1.exp[i] ,				
										loc_ctrl_1.fb[i] ,			
										&loc_arg_1[i], 
										&loc_val_1[i],	
										50,
										10 *flag.taking_off			
										 )	;	
			
			
			PID_calculate( dT_ms*1e-3f,            
										loc_ctrl_1.exp[i] ,				
										loc_ctrl_1.exp[i] ,				
										fb_speed_fix[i] ,			
										&loc_arg_1_fix[i], 
										&loc_val_1_fix[i],	
										50,
										10 *flag.taking_off			
										 )	;	
			
			loc_ctrl_1.out[i] = loc_val_1[i].out + loc_val_1_fix[i].out;	
		}		


	}

#define ATT_STAB 0
#define LOC_HOLD 1
static float exp_rol_tmp,exp_pit_tmp;
struct {float exp_rol_adj,exp_pit_adj,exp_rol,exp_pit;} att_2l_ct;
void Att_Angles_Reference(float dT_s){
	
	exp_rol_tmp = - loc_ctrl_1.out[Y];
	exp_pit_tmp = - loc_ctrl_1.out[X];
	
	if(flag.flight_mode == ATT_STAB)
	{
		if(ABS(exp_rol_tmp + att_2l_ct.exp_rol_adj) < 5)
		{
			att_2l_ct.exp_rol_adj += 0.2f *exp_rol_tmp *dT_s;
			att_2l_ct.exp_rol_adj = LIMIT(att_2l_ct.exp_rol_adj,-1,1);
		}
		
		if(ABS(exp_pit_tmp + att_2l_ct.exp_pit_adj) < 5)
		{
			att_2l_ct.exp_pit_adj += 0.2f *exp_pit_tmp *dT_s;
			att_2l_ct.exp_pit_adj = LIMIT(att_2l_ct.exp_pit_adj,-1,1);
		}
	}
	else
	{
		att_2l_ct.exp_rol_adj = 
		att_2l_ct.exp_pit_adj = 0;
	}
	
	
	att_2l_ct.exp_rol = exp_rol_tmp + att_2l_ct.exp_rol_adj;
	att_2l_ct.exp_pit = exp_pit_tmp + att_2l_ct.exp_pit_adj;
	
	
	att_2l_ct.exp_rol = LIMIT(att_2l_ct.exp_rol,-MAX_ANGLE,MAX_ANGLE);
	att_2l_ct.exp_pit = LIMIT(att_2l_ct.exp_pit,-MAX_ANGLE,MAX_ANGLE);
	

	
	}
void Loc_Manual_Reference(){loc_ctrl_1.out[X] = (float)MAX_ANGLE/MAX_SPEED *fs.speed_set_h[X] ;loc_ctrl_1.out[Y] = (float)MAX_ANGLE/MAX_SPEED *fs.speed_set_h[Y] ;}

int main(int argc,char**argv){
 int ms=0,arm,c1,c2,c3,flow;float h,v,a,collective;int prior_arm=0;
 Ano_Parame.set.pid_alt_1level[0]=2;Ano_Parame.set.pid_alt_1level[1]=1;Ano_Parame.set.pid_alt_1level[2]=.05f;
 Ano_Parame.set.pid_alt_2level[0]=1;
 Ano_Parame.set.auto_take_off_height=60;Ano_Parame.set.auto_take_off_speed=80;
 Ano_Parame.set.auto_landing_speed=60;Ano_Parame.set.idle_speed_pwm=20;
 Alt_1level_PID_Init();Alt_2level_PID_Init();imu_data.z_vec[2]=1;
 Ano_Parame.set.pid_loc_1level[0]=.15f;Ano_Parame.set.pid_loc_1level[1]=.10f;
 while(scanf("%d %d %d %d %d %f %f %f %f",&arm,&c1,&c2,&c3,&flow,&h,&v,&a,&collective)==9){
  ++ms;
  if(!arm){flag.unlock_sta=flag.unlock_cmd=0;}
  else if(!prior_arm){flag.unlock_sta=flag.unlock_cmd=2;}
  else if(c3>1200){flag.unlock_sta=flag.unlock_cmd=1;}
  prior_arm=arm;
  CH_N[0]=c1-1500;CH_N[1]=c2-1500;CH_N[2]=c3-1500;
  flag.thr_low=c3<=1150;switchs.of_flow_on=flow;
  if(argc>1 && argv[1][0]=='m'){flag.flight_mode=flow?LOC_HOLD:ATT_STAB;switchs.of_flow_on=0;}
  wcz_hei_fus.out=h;wcz_spe_fus.out=v;imu_data.w_acc[2]=a;
  if(argc>1 && argv[1][0]=='x'){of_rdf.gnd_vel_est_h[0]=v;of_rdf.gnd_vel_est_h[1]=-a;wcz_spe_fus.out=0;imu_data.w_acc[2]=0;}
  // State oracle externally supplies previous Alt1 thrust, as on the board.
  if(argc>1)mc.ct_val_thr=collective;
  Flight_State_Task(1,CH_N);
  if(ms%2==0)Motor_Ctrl_Task(2);
  if(argc>1 && argv[1][0]=='m' && ms%6==0)Att_Angles_Reference(.006f);
  if(ms%11==0){Alt_1level_Ctrl(.011f);Alt_2level_Ctrl(.011f);}
  if(argc>1 && argv[1][0]=='x' && ms%20==0 && flow)Loc_OF_Reference(20);
  if(argc>1 && argv[1][0]=='m' && ms%20==0)Loc_Manual_Reference();
  printf("%d %d %d %d %d %d %.9g %.9g %.9g %.9g %.9g %d %.9g %.9g %.9g %.9g %.9g %.9g %.9g %.9g %.9g\n",ms,flag.motor_preparation,flag.taking_off,flag.flying,flag.unlock_cmd==0,flag.auto_take_off_land,fs.speed_set_h[2],fs.speed_set_h_norm_lpf[2],fs.speed_set_h[0],fs.speed_set_h[1],mc.ct_val_thr,fs.alt_ctrl_speed_set,loc_ctrl_2.exp[2],err_i_comp,loc_ctrl_1.out[0],loc_ctrl_1.out[1],loc_val_1_fix[0].err_i,att_2l_ct.exp_rol,att_2l_ct.exp_pit,att_2l_ct.exp_rol_adj,att_2l_ct.exp_pit_adj);
 }
 return 0;
}
