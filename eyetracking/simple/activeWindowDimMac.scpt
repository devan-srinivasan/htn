global frontApp, windowSize, windowPosition

set windowTitle to ""
tell application "System Events"
    set frontApp to first application process whose frontmost is true
    set frontAppName to name of frontApp
    tell process frontAppName
        repeat until exists of ¬
            (1st window whose value of attribute "AXMain" is true)
            delay 3
        end repeat
        tell (1st window whose value of attribute "AXMain" is true)
            set windowSize to value of attribute "AXSize"
            set windowPosition to value of attribute "AXPosition"
        end tell
    end tell
end tell

return {windowSize, windowPosition}