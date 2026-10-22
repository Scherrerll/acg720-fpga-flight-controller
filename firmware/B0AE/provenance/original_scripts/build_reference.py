"""Build a host oracle from unchanged ANO function bodies, not an RTL model."""
from pathlib import Path
import re,os,subprocess,json,hashlib
R=Path(__file__).resolve().parent
def read(name):return (R/'reference'/name).read_bytes().decode('gb18030',errors='replace')
def function(name,file):
 s=read(file);m=re.search(r'(?m)^(?:static\s+)?(?:void|float)\s+'+name+r'\s*\(',s)
 assert m,name
 begin=s.index('{',m.start());level=1;i=begin+1
 while level:
  if s[i]=='{':level+=1
  if s[i]=='}':level-=1
  i+=1
 # Strip comments only, retain every executable token of the original body.
 return re.sub(r'/\*.*?\*/|//[^\n]*','',s[m.start():i],flags=re.S)
def block(file,marker):
 s=read(file);a=s.index('{',s.index(marker));i=a+1;level=1
 while level:
  if s[i]=='{':level+=1
  if s[i]=='}':level-=1
  i+=1
 return re.sub(r'/\*.*?\*/|//[^\n]*','',s[a+1:i-1],flags=re.S)
stub=r'''
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
'''
functions=[('my_sqrt_reciprocal','Ano_Math.c'),('my_sqrt','Ano_Math.c'),
 ('my_deadzone','Ano_Math.c'),('length_limit','Ano_Math.c'),
 ('PID_calculate','Ano_Pid.c'),('land_discriminat','Ano_FlightCtrl.c'),
 ('Flight_State_Task','Ano_FlightCtrl.c')]
body=stub+'\n'+'\n'.join(function(*v)for v in functions)
alt=read('Ano_AltCtrl.c');alt=re.sub(r'^#include[^\n]*','',alt,flags=re.M);alt=re.sub(r'/\*.*?\*/|//[^\n]*','',alt,flags=re.S)
motor=read('Ano_MotorCtrl.c');a=motor.index('s16 motor[');b=motor.index('void Motor_Ctrl_Task');decl=motor[a:b].replace('_mc_st mc;','')
body+='\n'+alt+'\n'+decl+'\n'+function('Motor_Ctrl_Task','Ano_MotorCtrl.c')
body+=r'''
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
'''
body+='void Loc_1level_PID_Init(){'+block('Ano_LocCtrl.c','else if(mode_f[1] == 1)')+'}\n'
body+='void Loc_OF_Reference(u16 dT_ms){'+block('Ano_LocCtrl.c','else if(switchs.of_flow_on && (!switchs.gps_on))')+'}\n'
att=read('Ano_AttCtrl.c');a=att.index('{',att.index('void Att_2level_Ctrl'));b=att.index('if(flag.speed_mode',a)
prefix=re.sub(r'/\*.*?\*/|//[^\n]*','',att[a+1:b],flags=re.S)
body+='\n#define ATT_STAB 0\n#define LOC_HOLD 1\nstatic float exp_rol_tmp,exp_pit_tmp;\nstruct {float exp_rol_adj,exp_pit_adj,exp_rol,exp_pit;} att_2l_ct;\n'
body+='void Att_Angles_Reference(float dT_s){'+prefix+'}\n'
loc=read('Ano_LocCtrl.c');loc=re.sub(r'/\*.*?\*/|//[^\n]*','',loc,flags=re.S)
manual=re.findall(r'loc_ctrl_1\.out\[[XY]\]\s*=\s*\(float\)MAX_ANGLE/MAX_SPEED[^;]+;',loc)[-2:]
assert len(manual)==2
body+='void Loc_Manual_Reference(){'+''.join(manual)+'}\n'
body+=r'''
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
'''
p=R/'tests/reference_oracle.cpp';p.write_text(body,encoding='utf8')
vc=Path('C:/softwares/Microsoft Visual Studio 12.0/VC')
sdk=Path('C:/Program Files (x86)/Windows Kits/8.1')
env=dict(os.environ,INCLUDE=';'.join(map(str,[vc/'include',sdk/'Include/um',sdk/'Include/shared'])),
 LIB=';'.join(map(str,[vc/'lib/amd64',sdk/'Lib/winv6.3/um/x64'])))
cmd=[str(vc/'bin/amd64/cl.exe'),'/nologo','/TP','/Od','/fp:strict',str(p),'/Fe'+str(R/'tests/reference_oracle.exe'),'/Fo'+str(R/'tests/reference_oracle.obj')]
result=subprocess.run(cmd,env=env,capture_output=True,text=True)
(R/'tests/reference_compile.log').write_text(result.stdout+result.stderr)
if result.returncode:raise RuntimeError(result.stdout+result.stderr)
print('Original ANO C-function oracle compiled')
