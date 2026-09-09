<!-- 1. env for google api ✅
2. get langgraph running with simple example ✅
3. get gemini llm api running ✅
4. search online on how to use old repo to factorise it in new one ✅
5. Separate Agents by two folders
general and Specialist agents categories ✅
6. Build Resource State in General category/folder ✅
7. Build Test case for main.py  ✅
9. Build Test for Resource State ✅
10. set up YAML ✅
11. write nginx set up here ✅
12. install uvicorn ✅ 
13. set up devops to AWS ✅ -->
<!-- 14. Fix build compile minor bug for summary agent ✅
15. write simple unit test case for summary agent to check if document type is Doc not string ✅ -->

<!-- 16. remove tut directory ✅
17. merge branch into main branch ✅
18. create new branch for translation agent ✅
19. Copy from Old repo translation agent code into here ✅
20. check that LLM is not tasked to return Document data type ✅
21. test translation agent manually ✅
22. write test case for Translation agent to make sure it works  ✅
23. Fix the bug discovered in translation agent, it doesn't return str, it returns  `isinstance([{'type': 'text', 'text': 'Each morning, the city sl..` ✅
23. make sure Translation Agent returns str as final output  ✅ -->

24. fix path issue for test.py, it happened after merge ImportError while importing test module '/home/runner/work/e-commerical-langgraph-fastapi/e-commerical-langgraph-fastapi/src/e_commerical_langgraph_fastapi/tests/graphs/general_agents/test_summary_agent.py'.
error happened due to probably change of import, have to make sure uv test, in pythonpath for uv pytomal starts same as python3 -m
25. slight modify main.py to return different string instead of hello world to hello duck, to make sure when we build and deploy it works on live
26. merge and create pull request for create_translation_agent branch
