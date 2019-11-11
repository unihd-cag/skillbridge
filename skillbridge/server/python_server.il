let((_filename _baseName _moduleFolder _installName _logName)

    _filename = get_filename(piport)
    _filename = pcreReplace(pcreCompile("^ +| +$") _filename "" 0)
    _baseName = substring(_filename 1 strlen(_filename)-2)
    _moduleFolder = substring(_filename 1 strlen(_filename)-23)
    _installName = strcat(_moduleFolder "client/definitions.txt")
    _executable = strcat("python '" _baseName "py'")
    _logName = strcat(_baseName "py.log")

    putd('pyDumpFunctionDefinitions nil)
    defun(pyDumpFunctionDefinitions (filename)
        let((code functions total aliases progress)
            poport = outfile(if(filename == "<install>" pyDumpFunctionDefinitions.installName filename))
            functions = listFunctions("[a-z]+[A-Z][a-zA-Z]+")
            total = length(functions)
            progress = 0
            foreach(func functions
                printf("BEGIN FUNCTION %s\n", func)
                code = sprintf(nil "help(%s)" func)
                errset(evalstring(code))
                aliases = listAlias(func)
                if(aliases != nil then
                    printf("ALIASES %L\n", aliases)
                )
                printf("END FUNCTION %s\n\n" func)

                progress = progress + 1

                if(mod(progress 100) == 0 then
                    fprintf(stdout "dumped %6.2f%% found %d functions\n" (progress * 100.0 / total) progress)
                )
            )
           fprintf(stdout "finished with %d functions total" progress)
        )
        close(poport)
        poport = stdout
        t
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
                    ipcWriteProcess(pyStartServer.ipc sprintf(nil "success %s\n" __pySkillToPython(result)))
                )
            )
        )
    )

    putd('__pyOnError nil)
    defun(__pyOnError (id data)
        fprintf(stderr "error %L\n" data)
    )

    putd('__pyOnFinish nil)
    defun(__pyOnFinish (id data)
        printf("server was stopped with code %L\n" data)
        deleteFile(pyStartServer.file)
        pyStartServer.ipc = nil
        remExitProc('__pyDeleteSocketOnExit)
    )

    putd('__pyPropertyListToPython nil)
    defun(__pyPropertyListToPython (propList)
        strcat("{"
            buildString(
                mapcar(lambda((key)
                    sprintf(nil "'%s':%s" key __pySkillToPython(get(propList key))))
                    propList->?)
            ",")
            "}"
        )
    )

    putd('__pySaveToVariableAndReturn nil)
    defun(__pySaveToVariableAndReturn (thing)
        let((repr variableName split objectType address)
            repr = sprintf(nil "%L" thing)
            if(rexExecute(repr) then
                split = parseString(repr ":")
                objectType = car(split)
                address = cadr(split)
                variableName = sprintf(nil "__py_%s_%s" objectType address)
                set(stringToSymbol(variableName) thing)
                sprintf(nil "Remote(%L)" variableName)
            else sprintf(nil "error(%L)" repr)
            )
        )
    )

    putd('__pyListToPython nil)
    defun(__pyListToPython (thing)
        strcat(
            "["
            buildString(mapcar('__pySkillToPython thing) ",")
            "]"
        )
    )

    putd('__pySkillToPython nil)
    defun(__pySkillToPython (thing)
        if(thing == t then "True" else
        if(thing == nil then "None" else
        if(or(numberp(thing) stringp(thing)) then sprintf(nil "%L" thing) else
        if(symbolp(thing) then sprintf(nil "Symbol('%s')" thing) else
        if(listp(thing) then
            if(and(car(thing) == nil symbolp(cadr(thing)))
            then __pyPropertyListToPython(thing)
            else __pyListToPython(thing)
            )
        else
        rexCompile("^[a-zA-Z]+:[x0-9a-f]+$")
        __pySaveToVariableAndReturn(thing)
        )))))
    )

    putd('pyStartServer nil)
    defun(pyStartServer (@key (id "default") (logLevel "WARNING") (singleMode nil) (timeout nil))

        if(pyStartServer.ipc != nil then
            fprintf(stderr, "server is already running\n")
            nil
        else
            let((executableWithArgs socketFile)
                socketFile = sprintf(nil "/tmp/skill-server-%L.sock"  id)

                if(isFileName(socketFile) then
                    fprintf(stderr, "Server cannot start, because %s already exists. Delete the file if you are sure that it is not in use anymore.", socketFile)
                    nil
                else
                    executableWithArgs = buildString(list(pyStartServer.exe socketFile logLevel))
                    if(singleMode != nil then
                        executableWithArgs = strcat(executableWithArgs "--single")
                    )
                    if(timeout != nil then
                        executableWithArgs = sprintf(nil "%s --timeout %L" executableWithArgs timeout)
                    )

                    pyStartServer.ipc = ipcBeginProcess(executableWithArgs "" '__pyOnData '__pyOnError '__pyOnFinish "python_server.log")
                    pyStartServer.file = socketFile
                    regExitBefore('__pyDeleteSocketOnExit)
                    t
                )
            )
        )
    )

    putd('__pyDeleteSocketOnExit nil)
    defun(__pyDeleteSocketOnExit (@rest args)
        deleteFile(pyStartServer.file)
    )

    pyStartServer.ipc = nil
    pyStartServer.file = nil
    pyStartServer.exe = _executable

    printf("Available commands:\n")
    printf("\tpyStartServer ?id \"default\" ?logLevel \"WARNING\" ?singleMode nil ?timeout nil\n")
    printf("\tpyKillServer\n")
    printf("\tpyReloadScript\n")
    printf("\tpyShowLog [numberOfLines]\n")
    printf("\tpyDumpFunctionDefinitions filename\n")
)
