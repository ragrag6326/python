#!/bin/bash

function telegram {

    # method=sendMessage
    local method=$1
    
    telegram_api="https://api.telegram.org"
    token=""
    chat_id=""

    case "$method" in
    "sendMessage")
      local text=$2
      [[ -z $text ]] && {
        echo "方法為 $method 但缺少需要發送的文字訊息 $text"
        exit 1 
      }
      curl -X POST "$telegram_api/$token/$method" -d "chat_id=$chat_id&text=$text"
      ;;

    "sendPhoto")
      echo ""
      #curl -X POST "$telegram_api/$token/$method" -d "chat_id=$chat_id&text=$text"
      ;;

    *)

    esac

}


Uri="healthcheck"
MonitorPort=8080
HealthStatus=$(curl -s localhost:$MonitorPort/$Uri | jq -r '.status')


if [[ $HealthStatus != "ok" ]]; then
   echo "白名單驗證服務已關閉 ，正嘗試重新啟動服務"
    
fi

