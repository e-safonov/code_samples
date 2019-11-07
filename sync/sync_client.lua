cur_dir = getScriptPath()
package.path = package.path .. ";" .. cur_dir .. "\\?.lua"

local zmq             = require "zmq"
local json            = require "json_2"
local settings_parser = require "settings_parser"

local settings_file = "client_settings.json"
local settings = {}    -- таблица настроек скрипта
local events_q = {}    -- очередь событий

local stopped     = false

local context
local req_socket
local sub_socket
local sub_id
local positon

function connect()
--[[
    Готовим необходимые нам сокеты для подключения.
--]]
    context = zmq.init(1)

    local req_alert = "req get error"
    local sub_alert = "sub get error"
    req_socket = assert(context:socket(zmq.REQ), req_alert)
    sub_socket = assert(context:socket(zmq.SUB), sub_alert)

    req_alert = "req connect error"
    sub_alert = "sub connect error"
    local req_addr = settings.ip_addr .. ":" .. settings.req_port
    local sub_addr = settings.ip_addr .. ":" .. settings.sub_port
    assert(req_socket:connect(req_addr), req_alert)
    assert(sub_socket:connect(sub_addr), sub_alert)
    req_socket:setopt(zmq.LINGER, 0)
    sub_socket:setopt(zmq.LINGER, 0)
    sub_socket:setopt(zmq.SUBSCRIBE, "")
end

function OnInit()
    settings = settings_parser.read(settings_file)
    connect()
end

function main()
    local text = '<< Test ' .. tostring(settings.test_number)
    message(text)
    -- message("Current 0MQ version is " .. table.concat(zmq.version(), '.'))

    subscribe()
    while not stopped do
        receive_req()
        --ping()
        --get_position(sub_id)
        receive_sub()
        process_events()
        sleep(tonumber(settings.sleep_time))
        -- stopped = true
    end

    message(">> Exited")
end

function subscribe()
    local msg = {
        ["header"]   = "get_subscribe",
        ["firmid"]   = settings.firmid,
        ["account"]  = settings.account,
        ["sec_code"] = settings.sec_code
    }
    req_socket:send(json.encode(msg), zmq.NOBLOCK)
end

function unsubscribe()
    local msg = {
        ["header"] = "unsubscribe",
        ["sub_id"] = sub_id
    }
    req_socket:send(json.encode(msg))
end

function get_position(sub_id)

    if not sub_id then
        return
    end

    local msg = { ["header"] = "get_position", ["sub_id"] = sub_id }
    msg = json.encode(msg)
    req_socket:send(msg)
end

function ping()
    local msg = {
        ["header"] = "ping"
    }
    msg = json.encode(msg)
    req_socket:send(msg)
end

function receive_req()
    local msg = tostring(req_socket:recv(zmq.NOBLOCK))

    if msg ~= "nil" then
        message(msg)
        msg = json.decode(msg)
        table.sinsert(events_q, msg)
    end
end

function receive_sub()
    local msg = tostring(sub_socket:recv(zmq.NOBLOCK))

    if msg ~= "nil" then
        message(msg)
        msg = json.decode(msg)

        -- стандартная фильтрация сообщений zmq не справляется с json
        -- фильтруем сами по sub_id
        if msg.sub_id ~= sub_id then
            return
        end

        table.sinsert(events_q, msg)
    end
end

function process_events()

    while #events_q > 0 do
        local event = events_q[1]
        table.sremove(events_q, 1)

        if event.header == "subscribe" then
            sub_id = event.sub_id

        elseif event.header == "unsubscribe" then
            sub_id = nil
            message("unsubscribe")

        elseif event.header == "position" then          -- получаем позицию, которую запросили
            message(
                "Position " ..
                settings.firmid   .. ", "  ..
                settings.account  .. ", "  ..
                settings.sec_code .. " = " ..
                event.pos
            )
        elseif event.header == "pong" then              -- ответ на ping
            message("pong " .. settings.ip_addr)

        elseif event.header == "change_position" then   -- получаем изменённую позицию
            message(
                "Change position " ..
                settings.firmid    .. ", "  ..
                settings.account   .. ", "  ..
                settings.sec_code  .. " = " ..
                event.pos
            )
        else
            return
        end
    end
end

function close()
    req_socket:close()
    sub_socket:close()
    context:term()
end

function OnStop(...)
    unsubscribe()
    close()
    stopped = true
end
