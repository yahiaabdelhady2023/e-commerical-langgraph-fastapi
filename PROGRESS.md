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

# 9/14/2026
1. merged and created pull request for products_agent ✅
2. renamed create_products_agent.py to products_agent for name convention and tested unittest cases ✅
3. created branch for article_synthesizer ✅
4. created code and organised code for article_synthesizer ✅
5. created test cases in tests folder ✅
6. merged and created pull request ✅
7. learnt that i can add shortcut to uv, in pyproject.toml i added graph_shortcut module, which i can simply write uv run graph_shortcut and it will run graph.py for me, requirements way to write everything in that file graph.py around main() or some function
8. learnt that pythonpath=[
    "src/e_commerical_langgraph_fastapi",
] , pythonpath are for dealing with import issues not executing, if i add graph.py full path here uv run won't be able to find it , it is only
for importing path resolving issues, best i can do is uv run full graph.py path or best approach which i have done above is uv run graph_shortcut
9. learnt that culture agent in my code is self-sufficient which means it can run standalone without using any other agent, as it  has resources agents to fetch resources online
10. remove processed_resources_list check comment in unittest and commit ✅

# 9/15/2026

1. create products_classifer_agent branch ✅
2. copy code from old repo ✅
3. organise code with copilot ✅
4. test in graph.py ✅
5. make note of input and output format and key names ✅
6. write unittest case ✅
7. test unittest case manaully ✅
8. push ✅
9. merge and pull request ✅ 
10. check CI/CD pipeline and liveserver ✅
11. remove quick folder ✅
12. rename culture agent to article_synthesizer ✅


# 9/16/2026

1. fixed bug regarding github, it happened when i tried to merge and pull request with branch to main, it failed because my local repo didn't
sync with remote one, remote one was ahead of mine, next time i need to do git pull origin main before i merge, however i tackled this issue via
git config pull.rebase false, so this statement says merge the two divergent commits, and see if they can be merged successfully, and add commit,
aka treat them as a new single commit, rebase false means do not change history of commits, keep it as it is, so always do this it is safest option and standard option but to avoid running into this issue ensure you always do git pull origin main to make sure repo remotely == local repo
2. merged artciles_synthesizer branch change to main  ✅
3. added mirror bug fix branch and merged it, it removed quick folder used for testing ✅
4. product classifer agent underwent improvements, instead of just giving products_name_lists, with culture summary and articles summary 
it is now given products_name_list alongside information regarding items like description, price, etc... and rating ✅
5. tweaked test for product classifer agent ✅
6. created marketing agent branch ✅
7. organised code for marketing agent ✅
8. changed output variable name from `processed_candidates_list` to something more meaningful `marketing_scripts` ✅