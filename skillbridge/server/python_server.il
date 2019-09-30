let((_filename _baseName _moduleFolder _installName _logName)

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
            t
        )
    )

    pyDumpFunctionDefinitions.installName = _installName

    putd('pyKillServer nil)
    defun(pyKillServer ()
        if(pyStartServer.ipc == nil then
            printf("server was not running\n")
            nil
        else
            ipcKillProcess(pyStartServer.ipc)
            pyStartServer.ipc = nil
            deleteFile(pyStartServer.file)
            t
        )
    )

    putd('pyReloadScript nil)
    defun(pyReloadScript ()
        printf("killing the old server\n")
        pyKillServer()
        load(pyReloadServer.filename)
        t
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
        t
    )

    pyShowLog.logName = _logName

    putd('__pyOnData nil)
    defun(__pyOnData (id data)
        foreach(line parseString(data "\n")
            let((result)
                errset(result=evalstring(line))
                if((errset.errset) then
                    printf("command %L resulted in error %L\n" line errset.errset)
                    ipcWriteProcess(pyStartServer.ipc sprintf(nil "failure %L\n" errset.errset))
                else
                    ipcWriteProcess(pyStartServer.ipc sprintf(nil "success %L\n" result))
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

    putd('pyStartServer nil)
    defun(pyStartServer (@optional (id "default") (logLevel "WARNING"))
        if(pyStartServer.ipc != nil then
            fprintf(stderr, "server is already running\n")
            nil
        else
            let((executableWithArgs socketFile)
                socketFile = sprintf(nil "/tmp/skill-server-%s.sock"  id)

                if(isFileName(socketFile) then
                    fprintf(stderr, "Server cannot start, because %s already exists. Delete the file if you are sure that it is not in use anymore.", socketFile)
                    nil
                else
                    executableWithArgs = buildString(list(_executable socketFile logLevel))
                    pyStartServer.ipc = ipcBeginProcess(executableWithArgs "" '__pyOnData '__pyOnError '__pyOnFinish "python_server.log")
                    pyStartServer.file = socketFile
                    t
                )
            )
        )
    )

    pyStartServer.ipc = nil
    pyStartServer.file = nil

    printf("Available commands:\n")
    printf("\tpyStartServer [socketFile [logLevel]]\n")
    printf("\tpyKillServer\n")
    printf("\tpyReloadScript\n")
    printf("\tpyShowLog [numberOfLines]\n")
    printf("\tpyDumpFunctionDefinitions filename\n")
)
