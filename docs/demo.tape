Output docs/demo.gif

Set FontSize 14
Set Width 900
Set Height 600
Set Theme "Dracula"
Set Padding 20

Type "tokencost --help"
Enter
Sleep 2s

Type "tokencost log -m gpt-4o -i 1500 -o 500"
Enter
Sleep 1.5s

Type "tokencost log -m claude-sonnet-4 -i 2000 -o 800 -p my-chatbot"
Enter
Sleep 1.5s

Type "tokencost summary"
Enter
Sleep 2s

Type "tokencost estimate 'Hello world' gpt-4o"
Enter
Sleep 2s

Type "tokencost budget set 5.00 --period daily"
Enter
Sleep 1.5s

Type "tokencost budget status"
Enter
Sleep 2s

Type "tokencost models"
Enter
Sleep 3s
