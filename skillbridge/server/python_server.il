__py_filename = get_filename(piport)
__py_withoutExtension = substring(__py_filename 1 strlen(__py_filename)-2)
__py_moduleFolder = substring(__py_filename 1 strlen(__py_filename)-23)
__py_installFile = strcat(__py_moduleFolder "client/definitions.txt")
__py_python = strcat("python " __py_withoutExtension "py")
__py_pythonLog = strcat(__py_withoutExtension "py.log")


putd('dumpFunctionDefinitions nil)
defun(dumpFunctionDefinitions (filename)
    names = nil
    poport = outfile(if(filename == "<install>" __py_installFile filename))
    total = float(length(oblist))

    for(i 1 (length(oblist) - 1)
        ; apparently the symbol unbound is in oblist and when you assign unbound to a
        ; variable, the variable is indeed unbound and causes an error if used, wtf skill
        if(symbolToString(nth(i oblist)) != "unbound" then
            name = nth(i oblist)

            if(and(isCallable(name) substring(name 1 1) != "_") then
                ; this is a hack, because `help(name)` does not evaluate the variable
                ; `name` for some reason
                printf("BEGIN FUNCTION %s\n" name)
                code = sprintf(nil "help(%s)" name)
                errset(evalstring(code))
                printf("END FUNCTION %s\n\n" name)
                names = cons(name names)
            )
           )

        if(mod(i 100) == 0 then
            fprintf(stdout "dumped %6.2f%% found %d functions\n" (i / total * 100) length(names))
        )
    )
    close(poport)
    poport = stdout
    sprintf(nil "found %d functions total" length(names))
)

putd('killPythonServer nil)
defun(killPythonServer ()
    ipcKillProcess(__py_ipc)
)

putd('reloadPythonServer nil)
defun(reloadPythonServer (@optional (level "WARNING"))
    printf("killing the old server\n")
    killPythonServer()
    setShellEnvVar(strcat("LOG_LEVEL=" level))
    load(__py_filename)
    printf("Available commands:\n")
    printf("\tkillPythonServer\n")
    printf("\treloadPythonServer [log level]\n")
    printf("\tshowPythonLog [number of lines]\n")
)

putd('showPythonLog nil)
defun(showPythonLog (@optional (length 20))
    fin = infile(__py_pythonLog)
    lines = nil
    for(i 1 length
        lines = append1(lines "")
    )
    while(gets(line fin)
        lines = cdr(append1(lines line))
    )

    foreach(line lines
        printf("%s" line)
    )
    printf("")
)

putd('__py_onData nil)
defun(__py_onData (id data)
    foreach(line parseString(data "\n")
        errset(result=evalstring(line))
	if( (errset.errset)
            then
                printf("command %L resulted in error %L\n" line errset.errset)
                ipcWriteProcess(__py_ipc sprintf(nil "failure %L\n" errset.errset))
            else
                ipcWriteProcess(__py_ipc sprintf(nil "success %L\n" result))
        )
    )
)

putd('__py_onError nil)
defun(__py_onError (id data)
    printf("error %L\n" data)   		
    
)

putd('__py_onFinish nil)
defun(__py_onFinish (id data)
    printf("server was stopped with code %L\n" data)   		
)

__py_ipc = ipcBeginProcess(__py_python "" '__py_onData '__py_onError '__py_onFinish "python_server.log")
