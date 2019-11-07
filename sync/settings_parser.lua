--[[
    Модуль содержит функционал для преобразования
    JSON-файла настроек в таблицу Lua.
--]]
local settings_parser = {}
local json = require "json"

function settings_parser.read(file_name)

    if not file_name then
        file_name = "settings.json"
    end

    local file_path = cur_dir .. "\\" .. file_name
    local text_data = ''

    for line in io.lines(file_path) do
        text_data = text_data .. line
        -- message(line)
    end

    local settings = json.decode(text_data)
    return settings
end

return settings_parser