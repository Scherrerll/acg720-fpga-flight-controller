"""Local HTTP intent adapter; serial I/O belongs exclusively to Host.receive."""
import hmac
import json
import math
from urllib.parse import urlsplit
from xy_pi_control import XYPIError


def stopped_guard(state):
    if state.get('connected') is not True or state.get('fresh') is not True:
        return False, '遥测未连接或已过期，无法确认停机'
    data=state.get('data')
    if not isinstance(data,dict):return False,'停机状态未知'
    for key,label in [('armed','解锁'),('controller_enabled','控制运行'),('command_fresh','有效电机命令')]:
        if data.get(key) is not False:return False,label+'未明确关闭'
    info=state.get('flight_info')
    if state.get('flight_info_fresh') is not True or not isinstance(info,dict) or info.get('taking_off') is not False:
        return False,'起飞状态未知或正在起飞'
    if type(state.get('sequence')) is not int or info.get('sequence')!=state['sequence']:
        return False,'等待同组主帧与起飞状态'
    pwm=data.get('pwm_us')
    if not isinstance(pwm,list)or len(pwm)!=4 or any(type(v)not in(int,float)or not math.isfinite(v)or v!=1000 for v in pwm):
        return False,'四路实际上报 PWM 必须均为 1000 μs'
    if data.get('rc_valid') is True:
        channels=data.get('rc_us')
        if not isinstance(channels,list)or len(channels)<5 or type(channels[4])not in(int,float)or not math.isfinite(channels[4])or not 900<=channels[4]<1800:
            return False,'CH5 需保持低/中位，禁止预解锁高位'
    elif data.get('rc_valid') is not False:return False,'遥控资格未知'
    return True,'停机预检通过；最终写入仍由 FPGA 提交边沿裁决'


def control_status(host):
    host.pi.tick()
    value=host.pi.snapshot()
    can_query=bool(value['enabled']and value['connected']and value['source']=='SiK'and value['baud']==115200 and not value['busy'])
    reason=''
    if not value['enabled']:reason='未启用参数入口；按操作说明使用 --enable-xy-pi 启动'
    elif not value['connected']:reason='未连接无线串口'
    elif value['source']!='SiK' or value['baud']!=115200:reason='参数入口仅支持 SiK 115200；USB 镜像为只读'
    elif value['busy']:reason='正在处理上一笔请求'
    elif not value['supported']:reason='先查询并确认设备的 B0B4 参数功能'
    else:
        safe,reason=host.parameter_stopped_guard()
        if safe:reason=''
    value.update(can_query=can_query,can_set=bool(can_query and value['supported']and not reason),
                 block_reason=reason,persistence='本次上电有效，重启恢复 P=0.1000 / I=0.0350',
                 scope='共享 XY 速度外环；FPGA 是最终写入裁决者')
    return value


def handle_get(handler,host,route):
    if route=='/api/xy-pi/session':
        if handler.headers.get('Sec-Fetch-Site')=='cross-site':handler.json_response(403,dict(code='origin',error='仅允许本地同源页面'));return True
        handler.json_response(200,dict(token=host.pi_token));return True
    if route=='/api/xy-pi/status':handler.json_response(200,control_status(host));return True
    return False


def handle_post(handler,host):
    route=urlsplit(handler.path).path
    if not route.startswith('/api/xy-pi/'):return False
    def fail(status,code,message):handler.json_response(status,dict(code=code,error=message))
    allowed={f'http://127.0.0.1:{handler.server.server_port}',f'http://localhost:{handler.server.server_port}'}
    if not handler.local_host()or handler.headers.get('Origin')not in allowed or handler.headers.get('Sec-Fetch-Site')in('cross-site','same-site'):
        fail(403,'origin','参数操作仅接受本地同源页面');return True
    token=handler.headers.get('X-XY-PI-Token','')
    if len(token)>200 or not token.isascii()or not hmac.compare_digest(token,host.pi_token):fail(403,'token','会话已变化，请刷新页面后重新查询');return True
    if handler.headers.get('Transfer-Encoding')or handler.headers.get('Content-Encoding'):
        fail(400,'body','不支持传输或内容编码');return True
    lengths=handler.headers.get_all('Content-Length')or[]
    if len(lengths)!=1 or not 1<=len(lengths[0])<=4 or not lengths[0].isascii()or not lengths[0].isdigit()or not 0<int(lengths[0])<=2048 or handler.headers.get_content_type()!='application/json':
        fail(400,'body','请求必须是有界 JSON');return True
    if route not in('/api/xy-pi/query','/api/xy-pi/set'):
        fail(404,'route','未知参数操作');return True
    try:
        def invalid_constant(_):raise ValueError('禁止非有限 JSON 数值')
        def unique_object(pairs):
            result={}
            for key,value in pairs:
                if key in result:raise ValueError('JSON 字段不可重复')
                result[key]=value
            return result
        data=json.loads(handler.rfile.read(int(lengths[0])),parse_constant=invalid_constant,object_pairs_hook=unique_object)
        keys={'request_id','epoch'}if route.endswith('/query')else{'request_id','epoch','expected_generation','p','i','confirmed_stopped'}
        if not isinstance(data,dict)or set(data)!=keys:raise ValueError('请求字段不符')
        if type(data['epoch'])is not int or type(data['request_id'])is not str:raise ValueError('请求标识或会话格式错误')
        if route.endswith('/query'):
            operation=host.pi.request_get(data['request_id'],data['epoch'])
        else:
            if data['confirmed_stopped']is not True:raise ValueError('请先确认拆桨停机与 CH5 低/中位')
            if type(data['p'])is not str or type(data['i'])is not str or type(data['expected_generation'])is not int:raise ValueError('P/I 必须为十进制文本，generation 必须为整数')
            safe,reason=host.parameter_stopped_guard()
            if not safe:fail(403,'not_stopped',reason);return True
            operation=host.pi.request_set(data['p'],data['i'],data['request_id'],data['expected_generation'],data['epoch'])
        handler.json_response(202,dict(operation_id=operation));return True
    except XYPIError as exc:
        code=exc.code;message=str(exc)
        status=409 if code in('busy','stale','stale_generation','epoch','request_conflict')else 503 if code in('disabled','not_connected','notconnected','unsupported','transport')else 400
        fail(status,code,message);return True
    except (ValueError,TypeError,KeyError,json.JSONDecodeError)as exc:
        fail(400,'invalid',str(exc));return True
