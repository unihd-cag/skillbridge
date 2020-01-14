let((_filename _baseName _moduleFolder _installName _logName)

    _filename = get_filename(piport)
    _filename = pcreReplace(pcreCompile("^ +| +$") _filename "" 0)
    _baseName = substring(_filename 1 strlen(_filename)-2)
    _moduleFolder = substring(_filename 1 strlen(_filename)-23)
    _installName = strcat(_moduleFolder "client/definitions.txt")
    _executable = strcat("\"" _baseName "py\"")
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
            let((result capturedWarning pythonCode)
                capturedWarning = __pyCaptureWarnings(errset(result=evalstring(line)))
                if((errset.errset) then
                    printf("command %L resulted in error %L\n" line errset.errset)
                    ipcWriteProcess(id sprintf(nil "failure %L\n" errset.errset))
                else
                    pythonCode = __pySkillToPython(result)
                    if((capturedWarning != "") then
                        pythonCode = sprintf(nil "warning(%L, %s)" capturedWarning pythonCode)
                    )
                    ipcWriteProcess(id sprintf(nil "success %s\n" pythonCode))
                )
            )
        )
    )

    putd('__pyOnError nil)
    defun(__pyOnError (id data)
        fprintf(stderr "ERROR %s\n" data)
    )

    putd('__pyOnFinish nil)
    defun(__pyOnFinish (id data)
        printf("server was stopped with code %L\n" data)
        pyStartServer.ipc = nil
    )

    putd('__pyOnFinishScript nil)
    defun(__pyOnFinishScript (id data)
        printf("script finished with code %L\n" data)
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
                split = buildString(parseString(repr "_") "")
                split = buildString(parseString(split "@") ":")
                split = parseString(split ":")
                objectType = car(split)
                address = cadr(split)
                variableName = sprintf(nil "__py_%s_%s" objectType address)
                set(stringToSymbol(variableName) thing)
                sprintf(nil "Remote(%L)" variableName)
            else
                sprintf(nil "error(%L)" repr)
                printf("I COULD NOT PARSE %L\n" repr)
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
        rexCompile("^[_a-zA-Z]+[:@][x0-9a-fA-F]+$")
        __pySaveToVariableAndReturn(thing)
        )))))
    )

    putd('__pyCaptureWarnings nil)
    defmacro(__pyCaptureWarnings (@rest body)
        `let(((tempPort outstring()))
            unwindProtect(
                {
                    let(((woport tempPort))
                        ,@body
                        ; next two lines are to force final warning to be flushed
                        warn("")
                        getWarn()
                    )
                    getOutstring(tempPort)
                }
                close(tempPort)
            )
        )
    )

    putd('pyStartServer nil)
    defun(pyStartServer (@key (id "default") (logLevel "WARNING") (singleMode nil) (timeout nil) (python "python"))

        if(pyStartServer.ipc != nil then
            fprintf(stderr, "server is already running\n")
            nil
        else
            executableWithArgs = sprintf(nil "%s %L %s" pyStartServer.exe id logLevel)
            if(singleMode != nil then
                executableWithArgs = strcat(executableWithArgs "--single")
            )
            if(timeout != nil then
                executableWithArgs = sprintf(nil "%s --timeout %L" executableWithArgs timeout)
            )
            executableWithArgs = sprintf(nil "\"%s\" %s" python executableWithArgs)

            pyStartServer.ipc = ipcBeginProcess(executableWithArgs "" '__pyOnData '__pyOnError '__pyOnFinish "python_server.log")           
            t
        )
    )

    putd('pyRun nil)
    defun(pyRunScript (script @key (python "python") (args nil))
        let((command)
            command = sprintf(nil "%s %s %s" python script buildString(args))
            ipcBeginProcess(command "" '__pyOnData '__pyOnError '__pyOnFinishScript "python_script.log")
        )
    )

    pyStartServer.ipc = nil
    pyStartServer.exe = _executable

    printf("Available commands:\n")
    printf("\tpyStartServer ?id \"default\" ?logLevel \"WARNING\" ?singleMode nil ?timeout nil ?python \"python\"\n")
    printf("\tpyKillServer\n")
    printf("\tpyReloadScript\n")
    printf("\tpyShowLog [numberOfLines]\n")
    printf("\tpyDumpFunctionDefinitions filename\n")
    printf("\tpyRun path ?args list() ?python \"python\"\n")
)
