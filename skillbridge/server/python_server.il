let((_filename _baseName _moduleFolder _installName _logName _ipc)

    _filename = get_filename(piport)
    _baseName = substring(_filename 1 strlen(_filename)-2)
    _moduleFolder = substring(_filename 1 strlen(_filename)-23)
    _installName = strcat(_moduleFolder "client/definitions.txt")
    _executable = strcat("python " _baseName "py")
    _logName = strcat(_baseName "py.log")

    putd('pyDumpFunctionDefinitions nil)
    defun(pyDumpFunctionDefinitions (filename)
        let((names name total code)
            names = nil
            total = float(length(oblist))
            poport = outfile(if(filename == "<install>" pyDumpFunctionDefinitions.installName filename))

            for(i 1 (length(oblist) - 1)
                ; apparently the symbol unbound is in oblist and when you assign unbound to a
                ; variable, the variable is indeed unbound and causes an error if used, wtf skill
                if(symbolToString(nth(i oblist)) != "unbound" then
                    name = nth(i oblist)

                    if(and(isCallable(name) substring(name 1 1) != "_") then
                        printf("BEGIN FUNCTION %s\n", name)
                        ; this is a hack, because `help(name)` does not evaluate the variable
                        ; `name` for some reason
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
    )

    pyDumpFunctionDefinitions.installName = _installName

    putd('pyKillServer nil)
    defun(pyKillServer ()
        ipcKillProcess(pyKillServer.ipc)
    )

    putd('pyReloadServer nil)
    defun(pyReloadServer (@optional (level "WARNING"))
        printf("killing the old server\n")
        pyKillServer()
        setShellEnvVar(strcat("LOG_LEVEL=" level))
        load(pyReloadServer.filename)
    )

    pyReloadServer.filename = _filename

    putd('pyShowLog nil)
    defun(pyShowLog (@optional (length 20))
        let((fin line lines)
            fin = infile(pyShowLog.logName)
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
    )

    pyShowLog.logName = _logName

    putd('__pyOnData nil)
    defun(__pyOnData (id data)
        foreach(line parseString(data "\n")
            let((result)
                errset(result=evalstring(line))
                if((errset.errset) then
                    printf("command %L resulted in error %L\n" line errset.errset)
                    ipcWriteProcess(__pyOnData.ipc sprintf(nil "failure %L\n" errset.errset))
                else
                    ipcWriteProcess(__pyOnData.ipc sprintf(nil "success %L\n" result))
                )
            )
        )
    )

    putd('__pyOnError nil)
    defun(__pyOnError (id data)
        printf("error %L\n" data)
    )

    putd('__pyOnFinish nil)
    defun(__pyOnFinish (id data)
        printf("server was stopped with code %L\n" data)
    )

    _ipc = ipcBeginProcess(_executable "" '__pyOnData '__pyOnError '__pyOnFinish "python_server.log")

    __pyOnData.ipc = _ipc
    pyKillServer.ipc = _ipc

    printf("Server started\n")
    printf("Available commands:\n")
    printf("\tpyKillServer\n")
    printf("\tpyReloadServer [logLevel]\n")
    printf("\tpyShowLog [numberOfLines]\n")
    printf("\tpyDumpFunctionDefinitions filename\n")
)
