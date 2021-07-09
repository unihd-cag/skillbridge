mkdir -p "${PREFIX}/lib/skill/skillbridge"

cp -f "${RECIPE_DIR}/../skillbridge.init.il" \
       "${PREFIX}/lib/skill/skillbridge/skillbridge.init.il"

cp -f "${RECIPE_DIR}/../skillbridge/server/python_server.il" \
       "${PREFIX}/lib/skill/skillbridge/python_server.il"

$PYTHON setup.py install
