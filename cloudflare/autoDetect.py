import pandas as pd
from cloudflare import Cloudflare
import socket
import yaml
import ruamel.yaml

# TG Bot 告警群
chat_id = "chatid"
bottoken= "bottoken"

# 設定檢查的 socket Port
port = 80

raw_data_path = '/root/renewIP/raw_data.yml'
sync_data_path = '/root/renewIP/sync_data.yml'


def read_yaml (type):

    with open(f'/root/renewIP/{type}_data.yml', 'r') as stream:
        data = yaml.load(stream, Loader=yaml.CLoader)
    return data

def same():

    raw_data = read_yaml('raw')
    sync_data = read_yaml('sync')

    raw = []
    sync= []

    for proxy_server in raw_data:
        raw.append(proxy_server)


    for proxy_server in sync_data:
        sync.append(proxy_server)

    same = set(raw) & set(sync)
    return(list(same))

def diff():
    raw_data = read_yaml('raw')
    sync_data = read_yaml('sync')

    raw = []
    sync= []

    for proxy_server in raw_data:
        raw.append(proxy_server)

    for proxy_server in sync_data:
        sync.append(proxy_server)

    differ = set(sync) - set(raw)
    return(list(differ))

def main(cloudflare):

    alive_ip = []
    dead_proxy = []
    dead_ip = []

    raw_data = read_yaml('raw')

    for proxy_server in raw_data :

        raw_ip = raw_data[proxy_server]['ip']

        #建立 TCP 連線
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)  # 設定超時時間為  10s
        result = sock.connect_ex((raw_ip, port))

        # 檢查連線結果 result = 0 則表示有回應
        if result == 0:
            alive_ip.append(raw_ip)

        else:
            dead_proxy.append(proxy_server)


    if len(alive_ip) < 1 :
            message = (f'所有機器都無回應')
            print(message)
            cloudflare.tg_send(message , chat_id , bottoken)
            sock.close()
            exit()

    if len(dead_proxy) == 0 :
            print('機器正常')
            sock.close()
            exit()

    if len(dead_proxy) > 0 :
        for proxy_server in dead_proxy :
            raw_domian = raw_data[proxy_server]['domain']
            dead_ip = raw_data[proxy_server]['ip']
            message = (f'{proxy_server}機器:{dead_ip} 無回應 , {raw_domian}正嘗試切換到 {alive_ip[0]}')
            print(message)
            cloudflare.tg_send(message , chat_id,bottoken)

            try:
                # 讀取無回應機器的 域名list
                print(f'{raw_domian}切換中')
                cloudflare.auto_update( dead_ip=dead_ip , alive_ip=alive_ip[0] , domains=raw_domian)

            except Exception as err :
                message = (f' {proxy_server} 切換到 {alive_ip[0]} 失敗 \n錯誤訊息:{err}')
                cloudflare.tg_send(message , chat_id,bottoken)

            else:
                # 讀取 raw_Data 選裡面活的IP
                raw_data = read_yaml('raw')
                raw_data[proxy_server]['ip'] = alive_ip[0]
                with open(sync_data_path, 'w') as sync , open(raw_data_path, 'w') as raw :
                    yaml.dump(raw_data, sync)
                    yaml.dump(raw_data, raw)

                message = (f' {proxy_server} 成功切換到 {alive_ip[0]}')
                print(message)
                cloudflare.tg_send(message , chat_id,bottoken)

    # 關閉連線
    sock.close()

def sync_ip(cloudflare):

    raw_data = read_yaml('raw')
    sync_data = read_yaml('sync')

    same_domain = same()
    for proxy_server in same_domain :

        # 原始、同步檔案的 IP
        raw_ip = raw_data[proxy_server]['ip']
        sync_ip = sync_data[proxy_server]['ip']

        # 原始、同步檔案的 domain
        raw_domian = raw_data[proxy_server]['domain']
        sync_domain = sync_data[proxy_server]['domain']

        if raw_ip != sync_ip :  # 代表 sync 檔案 IP 有更動過
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)  # 設定超時時間為 5 秒
            result = sock.connect_ex((sync_ip, port))  # 同步檔案 ip有回應

            if result == 0:  # sync改過的IP 有回應後才會把檔案寫到 raw 檔案中
                if proxy_server == 'spareIP' :  # 如果只是改備用IP (spareIP) 同步過去就好不需要update
                    print('備用IP同步完成')
                    message = (f'原始備用IP:{raw_ip} 正在切換至 同步檔案IP:{sync_ip} ')
                    cloudflare.tg_send(message , chat_id,bottoken)
                    print(message)

                else:
                    message =(f'{proxy_server}原始IP:{raw_ip} 與同步IP:{sync_ip} 不一致正在切換中')
                    cloudflare.tg_send(message , chat_id,bottoken)
                    print(message)

                    # cloudflare.auto_update( dead_ip=None , alive_ip=sync_ip , domains=sync_domain )
                    message = (f'{proxy_server}原始IP:{raw_ip} 正在切換至 同步IP:{sync_ip} ')
                    cloudflare.tg_send(message , chat_id ,bottoken)
                    print(message)

        #     else:
        #         message = (f'同步檔案{proxy_server}的 IP:{sync_ip} 無回應請重新確認')
        #         raise Exception (message)

def sync_domain (cloudflare):
    
    raw_data = read_yaml('raw')
    sync_data = read_yaml('sync')

    same_domain = same()

    for proxy_server in same_domain :

        # 原始、同步檔案的 IP
        raw_ip = raw_data[proxy_server]['ip']
        sync_ip = sync_data[proxy_server]['ip']

        # 原始、同步檔案的 domain
        raw_domian = raw_data[proxy_server]['domain']
        sync_domain = sync_data[proxy_server]['domain']
        
        if raw_domian and sync_domain : 
            raw_long = len(raw_domian)
            sync_long = len(sync_domain)
            
            add_list = ''
            del_list = ''

            diff =  set(sync_domain) ^ set(raw_domian)
            if diff :
                if raw_long  < sync_long :
                    add_list = list(diff)
                    
                else:
                    del_list = list(diff)

            if add_list :
            #     # cloudflare.auto_update( dead_ip=None , alive_ip=sync_ip , domains=diff_domain )
                message = (f'{proxy_server} 新增的 {add_list} 正在添加至{sync_ip}')
                print(message)
                cloudflare.tg_send(message , chat_id,bottoken)

            if  del_list :
                message = (f'{proxy_server} 的 {del_list} 正在刪除')
                cloudflare.tg_send(message , chat_id,bottoken)
                print(message)

def sync_new(cloudflare):

    sync_data = read_yaml('sync')

    diff_domain = diff()
    if diff_domain:
        for proxy_server in diff_domain :

            sync_ip = sync_data[proxy_server]['ip']
            sync_domain = sync_data[proxy_server]['domain']
            # cloudflare.auto_update( dead_ip=None , alive_ip=sync_ip , domains=sync_domain )
            message = (f'新增 porxy : {proxy_server} 域名: {sync_domain} 正在添加至{sync_ip}')
            cloudflare.tg_send(message , chat_id , bottoken)
            print(message)

def sync (cloudflare):
    try :
        # 打開並讀取 raw yaml 檔案
        with open(raw_data_path, 'r') as raw:
            raw_data = yaml.safe_load(raw)

        # 打開並讀取 sync yaml 檔案
        with open(sync_data_path, 'r') as sync :
            sync_data = yaml.safe_load(sync)

        # 将合并后的键写入第一个 YAML 文件和第二个 YAML 文件中
        with open(raw_data_path, 'w') as raw:
            ruamel.yaml.dump(sync_data, raw, default_flow_style=False)
    except:
        message = (f'同步檔案失敗, 請重新確認')
        raise Exception (message)
    else:
        message = ('檔案同步完成')
        cloudflare.tg_send(message , chat_id , bottoken)


if __name__ == "__main__":

    """
    CF
    """
    cf_token = 'cf_token'
    cf_email = 'yours_email'


    account1 = Cloudflare( cf_token , cf_email )
    main(account1)

