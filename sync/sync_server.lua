cur_dir = getScriptPath()
package.path = package.path .. ";" .. cur_dir .. "\\?.lua"

local zmq             = require "zmq"
local json            = require "json_2"
local settings_parser = require "settings_parser"

local stopped     = false

local context
local rep_socket
local pub_socket

local settings_file = "server_settings.json"
local settings   = {}   -- таблица настроек скрипта
local events_q   = {}   -- очередь событий
local subscribes = {}   -- таблица паметров, по которым ищем позицию

function OnInit()
--[[
    Инициализуем нужные для запуска параметры.
--]]
    settings = settings_parser.read(settings_file)
    bind()
    math.randomseed(os.time())
end

function bind()
--[[
    Готовим необходимые нам сокеты для подключения.
--]]
    context = zmq.init(1)

    local rep_alert = "Can't get reply port."
    local pub_alert = "Can't get publisher port."
    rep_socket = assert(context:socket(zmq.REP), rep_alert)
    pub_socket = assert(context:socket(zmq.PUB), pub_alert)

    rep_alert = "Can't bind reply port."
    pub_alert = "Can't bind publisher port."
    local rep_addr = settings.ip_addr .. ":" .. settings.rep_port
    local pub_addr = settings.ip_addr .. ":" .. settings.pub_port
    assert(rep_socket:bind(rep_addr), rep_alert)
    assert(pub_socket:bind(pub_addr), pub_alert)
    rep_socket:setopt(zmq.LINGER, 0)
    pub_socket:setopt(zmq.LINGER, 0)
end

function main()
    local text = '<< Test ' .. tostring(settings.test_number)
    message(text)

    while not stopped do
        recieve()
        process_events()
        sleep(tonumber(settings.sleep_time))
        --stopped = true
    end

    message(">> Exited")
end

function recieve()
--[[
    Читаем сообщение и добавляем в очередь событий.
--]]
    local msg = tostring(rep_socket:recv(zmq.NOBLOCK))

    if msg ~= "nil" then
        msg = json.decode(msg)
        table.sinsert(events_q, msg)
    end
end

function process_events()
--[[
    Обрабатываем очередь событий.
--]]
    while #events_q > 0 do
        local event = events_q[1]
        table.sremove(events_q, 1)

        if event.header == "OnTrade" then
            change_position(event.trade)

        elseif event.header == "get_subscribe" then
            get_subscribe(event.firmid, event.account, event.sec_code)

        elseif event.header == "unsubscribe" then
            unsubscribe(event.sub_id)

        elseif event.header == "get_position" then
            local need_send = true
            get_position(event.sub_id, need_send)

        elseif event.header == "ping" then
            local msg = { ["header"] = "pong" }
            rep_socket:send(json.encode(msg), zmq.NOBLOCK)
        else
            return
        end
    end
end

function OnTrade(trade)
--[[
    При совершении сделки, добавляем соответствующее
    событие со всем содержимым в очередь для обработки.
--]]
    local event = { ["header"] = "OnTrade", ["trade"] = trade }
    table.sinsert(events_q, event)
end

function change_position(trade)

    local sub_id, sub = seach_subscribe(trade.firmid, trade.account, trade.sec_code)

    -- Проверяем имеется ли подписка на изменение позиции по сделке, и дополнительно
    -- проверяем и запоминаем номер последней сделки т.к. Quik любит отсылать
    -- callback-и дважды на одну и ту же хрень.
    if sub and subscribes[sub_id].last_trade ~= trade.trade_num then

        subscribes[sub_id].last_trade = trade.trade_num

        local need_send = false
        local pos = get_position(sub_id, need_send)
        local msg = {
            ["header"] = "change_position",
            ["pos"]    = pos,
            ["sub_id"] = sub_id,
        }
        pub_socket:send(json.encode(msg), zmq.NOBLOCK)
    end
end

function get_subscribe(firmid, account, sec_code)

    local sub_id, sub = seach_subscribe(firmid, account, sec_code)

    if sub_id and sub then
        subscribes[sub_id].clients_cnt = sub.clients_cnt + 1
    else
        sub_id = "id" .. tostring(math.random(1000))

        local new_sub = {
            ["firmid"]      = firmid,
            ["account"]     = account,
            ["sec_code"]    = sec_code,
            ["last_trade"]  = 0,
            ["clients_cnt"] = 1,
            [""] = 0
        }
        subscribes[sub_id] = new_sub
    end

    local msg = { ["header"] = "subscribe", ["sub_id"] = sub_id }
    rep_socket:send(json.encode(msg), zmq.NOBLOCK)
end

function seach_subscribe(firmid, account, sec_code)

    for k, v in pairs(subscribes) do
        if v.firmid   == firmid  and
           v.account  == account and
           v.sec_code == sec_code then

            return k, v
        end
    end
end

function unsubscribe(sub_id)
    subscribes[sub_id].clients_cnt = subscribes[sub_id].clients_cnt - 1

    if subscribes[sub_id].clients_cnt == 0 then
        subscribes[sub_id] = nil
    end

    local msg = {["header"] = "unsubscribe"}
    rep_socket:send(json.encode(msg), zmq.NOBLOCK)
end

function get_position(sub_id, need_send)
--[[
    Получаем позицию из таблицы "Позиций по клиентским счетам (фьючерсы)"
    рабочего места Quik.
--]]
    local sub = subscribes[sub_id]

    local type = 0
    local result = getFuturesHolding(
        sub.firmid,
        sub.account,  -- в таблице позиций называется trdaccid
        sub.sec_code,
        type
    )
    if result then
        if need_send then
            local msg = { ["header"] = "position", ["pos"] = tostring(result.totalnet) }
            rep_socket:send(json.encode(msg), zmq.NOBLOCK)
        else
            return result.totalnet
        end
    end
end

function close()
    rep_socket:close()
    pub_socket:close()
    context:term()
end

function OnStop(...)
--[[
    Обрабатываем остановку скрипта пользователем Quik.
--]]
    close()
    stopped = true
end
