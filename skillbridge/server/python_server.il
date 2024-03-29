let((_filename _baseName _moduleFolder _logDirectory _executable _unbound)

    _filename = get_filename(piport)
    _filename = pcreReplace(pcreCompile("^ +| +$") _filename "" 0)
    _baseName = substring(_filename 1 strlen(_filename)-2)
    _moduleFolder = substring(_filename 1 strlen(_filename)-23)
    _executable = strcat("\"" _baseName "py\"")
    _logDirectory = getShellEnvVar("SKILLBRIDGE_LOG_DIRECTORY") || "."
    _unbound = makeTable("JustForUnbound")[""]

    putd('pyKillServer nil)
    defun(pyKillServer ()
        if(!pyStartServer.ipc then
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
    defun(pyShowLog (@optional (length 20) "x")
        let((fin line (lines declare(lines[length])) (ptr 0))
            fin = infile(pyShowLog.logName)

            while(gets(line fin)
                lines[ptr] = line
                ptr = mod(ptr + 1 length)
            )

            for(i 0 length-1
                printf("%s" lines[mod(ptr + i length)])
            )
            printf("")
        )
        t
    )

    pyShowLog.logName = lsprintf("%s/skillbridge_skill.log" _logDirectory)

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

    putd('__pyOnData nil)
    defun(__pyOnData (id data)
        foreach(line parseString(data "\n")
            let((result capturedWarning pythonCode)
                capturedWarning = __pyCaptureWarnings(errset(result=evalstring(line)))
                if((errset.errset) then
                    printf("command %L resulted in error %L\n" line errset.errset)
                    ipcWriteProcess(id lsprintf("failure %L\n" errset.errset))
                else
                    if(boundp('result) then
                        pythonCode = __pySkillToPython(result)
                        if((capturedWarning != "" && capturedWarning != "*WARNING* ") then
                            pythonCode = lsprintf("warning(%L, %s)" capturedWarning pythonCode)
                        )
                        ipcWriteProcess(id lsprintf("success %s\n" pythonCode))
                    else
                        ipcWriteProcess(id "success error('unbound')\n")
                    )
                )
            )
        )
    )

    putd('__pyOnError nil)
    defun(__pyOnError (_ data)
        fprintf(stderr "PYTHON: %s\n" data)
    )

    putd('__pyOnFinish nil)
    defun(__pyOnFinish (_ data)
        printf("server was stopped with code %L\n" data)
        pyStartServer.ipc = nil
    )

    putd('__pyOnFinishScript nil)
    defun(__pyOnFinishScript (_ data)
        printf("script finished with code %L\n" data)
    )



    putd('__pyPropertyListToPython nil)
    defun(__pyPropertyListToPython (propList)
        strcat("{"
            buildString(
                mapcar(lambda((key)
                    lsprintf("'%s':%s" key __pySkillToPython(get(propList key))))
                    propList->?)
            ",")
            "}"
        )
    )

    putd('__pySaveToVariableAndReturn nil)
    defun(__pySaveToVariableAndReturn (thing)
        let((repr variableName split objectType address variableSymbol)
            repr = lsprintf("%L" thing)
            if(rexExecute(repr) then
                split = buildString(parseString(repr "_") "")
                split = parseString(split "@:")
                objectType = car(split)
                address = cadr(split)
                variableName = lsprintf("__py_%s_%s" objectType address)
                set(stringToSymbol(variableName) thing)
                lsprintf("Remote(%L)" variableName)
            else if(otherp(thing) then
                variableSymbol = gensym("__py_OTHER_")
                set(variableSymbol thing)
                lsprintf("Remote(%L)" symbolToString(variableSymbol))
            else if(portp(thing) then
                variableSymbol = gensym("__py_openfile_")
                set(variableSymbol thing)
                lsprintf("Remote(%L)" symbolToString(variableSymbol))
            else
                lsprintf("error(%L)" repr)
                printf("I COULD NOT PARSE %L\n" repr)
            )))
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

    putd('__pyVectorToPython nil)
    defun(__pyVectorToPython (collection)
        let((symbol)
            symbol = gensym("__py_vector_")
            set(symbol collection)
            lsprintf("Vector(%L)" symbolToString(symbol))
        )
    )

    putd('__pyTableToPython nil)
    defun(__pyTableToPython (collection)
        let((symbol)
            symbol = gensym("__py_table_")
            set(symbol collection)
            lsprintf("Table(%L)" symbolToString(symbol))
        )
    )

    putd('__pySkillToPython nil)
    defun(__pySkillToPython (thing)
        if(thing == t then "True" else
        if(!thing then "None" else
        if(or(numberp(thing) stringp(thing)) then lsprintf("%L" thing) else
        if(symbolp(thing) then lsprintf("Symbol('%s')" thing) else
        if(listp(thing) then
            if(and(!car(thing) symbolp(cadr(thing)) cadr(thing) != t)
            then __pyPropertyListToPython(thing)
            else __pyListToPython(thing)
            )
        else
        if(tablep(thing) then __pyTableToPython(thing) else
        if(vectorp(thing) then __pyVectorToPython(thing) else
        rexCompile("^[_a-zA-Z]+[:@][x0-9a-fA-F]+$")
        __pySaveToVariableAndReturn(thing)
        )))))))
    )

    putd('pyStartServer nil)
    defun(pyStartServer (@key (id "default") (logLevel "INFO") (singleMode nil) (timeout nil) (python "python") "ttggt")
        if(pyStartServer.ipc then
            fprintf(stderr, "server is already running\n")
            nil
        else
            let(((executableWithArgs lsprintf("%s %L %s" pyStartServer.exe id logLevel)))
                if(singleMode then
                    executableWithArgs = strcat(executableWithArgs "--single")
                )
                if(timeout then
                    executableWithArgs = lsprintf("%s --timeout %L" executableWithArgs timeout)
                )
                executableWithArgs = lsprintf("\"%s\" %s" python executableWithArgs)

                pyStartServer.ipc = ipcBeginProcess(executableWithArgs "" '__pyOnData '__pyOnError '__pyOnFinish pyStartServer.logName)
                t
            )
        )
    )

    pyStartServer.logName = lsprintf("%s/skillbridge_skill.log" _logDirectory)

    putd('pyRunScript nil)
    defun(pyRunScript (script @key (python "python") (args nil) (block nil) "ttlg")
        let((command process)
            command = lsprintf("%s %s %s" python script buildString(args))
            process = ipcBeginProcess(command "" '__pyOnData '__pyOnError '__pyOnFinishScript pyRunScript.logName)

            if(block then ipcWait(process) else process)
        )
    )

    pyRunScript.logName = lsprintf("%s/skillbridge_script.log" _logDirectory)

    pyStartServer.ipc = nil
    pyStartServer.exe = _executable

    printf("Available commands:\n")
    printf("\tpyStartServer ?id \"default\" ?logLevel \"WARNING\" ?singleMode nil ?timeout nil ?python \"python\"\n")
    printf("\tpyKillServer\n")
    printf("\tpyReloadScript\n")
    printf("\tpyShowLog [numberOfLines]\n")
    printf("\tpyRunScript path ?args list() ?python \"python\"\n")
)
