# Today's Progress

# 8/31/2026
- a year since I came back from the uk

# 9/7/2026
- fixed importError bug
- it was happening because of the following, python interpreter doesn't crawl inside root folder
even if i used -m, it only looks at direct stuff inside folder , e.g. 
if /e-commerical-langgraph-fastapi/src is in python path for interpreter to check it can check only
what inside of it directly not its subchildren so it is e_commerical_langgraph_fastapi folder,
so in python files we need to do e_commerical_langgraph.app.graphs.etc... to get it working, we need
full absolute path starting from folder or file interpreter can see and this is standard practice in python, with one tweak if you are working in same level importing module next to another one you should
use .. [relative import]


# 9/8/2026
1. Fix build compile minor bug for summary agent ✅
2. write simple unit test case for summary agent to check if it works ✅
3. checked that final output of summary agent is str
4. learnt that I shouldn't ask AI agent to return Document data type as output, as it will struggle, only str, then i manually in python convert it into Document, stick to primitive data types when using with_structured_output for LLM like 'int', 'float', 'str', 'list', 'dict'
5. Repository Maintenance & Branch Setup: Removed the legacy tut directory, merged the active branch into main, and created a dedicated feature branch for the translation agent.
6. Translation Agent Migration & Output Fixes: Migrated agent code from the old repository, wrote manual and automated test cases, and fixed an output format bug so the LLM cleanly returns a str instead of a list of content dictionaries or Document data types.

# 9/9/2026
1. fixed tiktoken bug missing when testing on github using CI, installed it using uv ✅
2. changed hello world in endpoint to hello carrot to check that liveserver CI/CD is working, and it is working ✅
3. create new branch create_products_agent ✅ 
4. copied create product agents code from old repo ✅
5. test create products agent, and it is working ✅

# 9/12/2026
1. fix documents not found for products agent testing, the two ones in documents folder ✅ via using -m flag in python
2. create unittest to test products agent ✅
3. unit test: Evaluate Whole Agent ✅
4. Unit test: Check if Python Validation Model is working for small json file ✅
5. Learnt that, python classes are not only defined by name and variables they have e.g. age, name, if you have two classes with same components
and same name, but in different location python will treat them differently, this is why when i tried to check if object created using
class that is identifical to product class from product_agent it failed when i did single_product == result["products_list"][0], it only worked
when i did one of the following
    - import product class from main file of product agent and use it to create single_product
    - use .model_dump() , single_product.model_dump() == result["products_list"][0].model_dump() which gets json values instead
6. learnt that uv run pytest, looks for test file in root, if not it will fail not because uv run pytest cannot find it, it can it is smart it searches all subdirectories for any file starts with test_*.py, but it will fail when you import things from app, which is why you need to include full path needed like -m when you run uv run for TEST specifically , you put app path to test in pyproject.toml,
e.g.  [tool.pytest.ini_options]
pythonpath=[
    "src/e_commerical_langgraph_fastapi"
]
7. to run a specific unittest using uv run pytest, you need to pass full path not just the relative name, if relative name doesn't work run full path