from typing import List, Union

import pandas as pd

from st_aggrid import AgGrid, GridOptionsBuilder

import streamlit as st
import diskcache
from oai_client import OAIClient
from settings import Settings
import utils

MODELS = [
    "text-davinci-002",
    "text-curie-001",
    "text-babbage-001",
    "text-ada-001",
    "code-davinci-002",
    "code-cushman-001",
]
# STOP_SEQUENCES = [
#     "Candidate:",
#     "Interviewer:",
#     "newline",
#     "double-newline",
#     "Human:",
#     "Assistant:",
#     "Q:",
#     "A:",
#     "INPUT",
#     "OUTPUT",
# ]
FEEDBACK_PROMPT = """
(End of interview)

Please provide feedback on the candidate's performance in the interview. Even if their resume is great
it's important to focus on their interview performance. If the chat is short and you don't have enough
information to provide feedback, please provide feedback on the resume instead. And explain that you 
would like to see more of the candidate in the interview.

Please include the following information:
* Candidates strengths
* Candidates weaknesses
* Overall conclusion
* Hire / No-Hire recommendation

Your feedback should be in the following format:

Strengths:

<list strengths here>

Weaknesses:

<list weaknesses here>

Conclusion:

<conclusion here>

Recommendation: <Hire / No-Hire>

YOUR FEEDBACK:
""".strip()

INITIAL_TRANSCRIPT = "Interviewer: Hi, how are you doing today?"

INITIAL_RESUME = """
Senior AI/Robotics Engineer
Cruise Automation · Full-time
Jun 2018 - Present · 4 yrs 6 mos
San Francisco Bay Area

* Full-stack machine learning from dataset generation to model deployment
* Co-founded our Machine Learning Platform team and led pod of 10+ engineers
* Architected lineage/metadata management service and experiment tracking UI
* Developed internal modeling framework to reduce boilerplate
* Developed data pipelines, data serialization tooling, and high-performance data loader
* Optimized large-scale distributed training jobs and debugged failures

Amazon
4 yrs 3 mos
Greater Seattle Area
Software Development Engineer
Apr 2015 - Nov 2016 · 1 yr 8 mos

• Zero-click Ordering, Amazon's recurring delivery platform
• Developed selection management service using NoSQL-based workflow approach
• Developed program to enable category-specific discount structures and extend Subscribe & Save to millions of products
• Java, DynamoDB, Oracle, SQS, S3, Spring
"""

INITIAL_QUESTION = """
System Design Interview

You are a Machine Learning Engineer at at a Digital Health Startup called Bright Labs. Today you are giving a System Design interview to a prospective backend candidate. Your job is to ask the candidate a system design question and then write up feedback on the candidate to share with the hiring committee

Background on you:
You work on the machine learning stack at Bright Labs, which involves training and deployment transformer based models to provide a chat-bot like service which helps answer users health questions.

Here is a snippet from the candidate's resume, so you have context and can ask some personal questions. And tailor the interview to the candidate's experiences.

CANDIDATE RESUME:

{{resume}}

(END OF RESUME)

The interview should adhere to the following format:

2 minutes - opening intros (share about yourself, and ask about the candidate)
3 minutes - ask the candidate to tell you about a system they've built at work
30 minutes - ask the candidate a system design question
5 minutes - ask the candidate if they have any questions for you

Here is the system design question you plan to ask:

Question: Design a type-ahead search engine service.
Problem: This service partially completes the search queries by displaying n number of suggestions for completing the query that the user intended to search.

Some clarifications (if the candidate asks or it feels appropriate to share):

0. What are the input and output of the system?
The input will be the beginning of a user search query, for example: "how to" and the output should be a list of likely auto completions: ["how to grill", "how to grill a hamburger", "how to play tennis"]

1. What is the data source for generating the suggestions?

We have data about historical queries and the frequency of that query, which can be simplified to:
query_id, query
1, how to grill a hamburger
2, how to play tennis
3, how to play tennis
4. how to play tennis well

2. What are the expected response time and throughput of this service?

Ideally within 1 second each time the user changes their query or types a new word or words.

3. How many suggestions need to be displayed in response to a query?

5 to 10 suggestions

Here are the rules for the conversation:
* You are a chat bot who conducts system design interviews
* Speak in first person and converse directly with the candidate
* Do not provide any backend context or narration. Remember this is a dialogue
* Do NOT write the candidates's replies, only your own
* We don't have access to a whiteboard, so the candidate can't draw anything. Only type/talk.

BEGIN!

{{transcript}}
""".strip()


@st.cache(ttl=60 * 60 * 24)
def init_oai_client(oai_api_key: str):
    cache = diskcache.Cache(directory="/tmp/cache")
    oai_client = OAIClient(
        api_key=oai_api_key,
        organization_id=None,
        cache=cache,
    )
    return oai_client


def run_completion(
    oai_client: OAIClient,
    prompt_text: str,
    model: str,
    stop: Union[List[str], None],
    max_tokens: int,
    temperature: float,
    best_of: int = 1,
):
    print("Running completion!")
    if stop:
        if "double-newline" in stop:
            stop.remove("double-newline")
            stop.append("\n\n")
        if "newline" in stop:
            stop.remove("newline")
            stop.append("\n")
    resp = oai_client.complete(
        prompt_text,
        model=model,  # type: ignore
        max_tokens=max_tokens,  # type: ignore
        temperature=temperature,
        stop=stop or None,
        best_of=best_of,
    )
    return resp


def main():
    utils.init_page_layout()
    session = st.session_state
    oai_client = init_oai_client(st.secrets["OPENAI_API_KEY"])

    if "transcript" not in session:
        session.transcript = [INITIAL_TRANSCRIPT]
        session.candidate_text = ""

    with st.sidebar:
        model = st.selectbox(
            "Model",
            MODELS,
            index=0,
        )
        max_tokens = st.number_input(
            "Max tokens",
            value=64,
            min_value=0,
            max_value=2048,
            step=2,
        )
        temperature = st.number_input(
            "Temperature", value=0.7, step=0.05
        )
        stop = ["Candidate:", "Interviewer:"]

    chat_tab, resume_tab, question_tab, feedback_tab = st.tabs(["Chat", "Resume", "Question", "Feedback"])

    with resume_tab:
        resume_text = resume_tab.text_area(
            "Candidate Resume",
            height=700,
            value=INITIAL_RESUME,
        )
    
    with question_tab:
        question_text = question_tab.text_area(
            "Question Prompt",
            height=700,
            value=INITIAL_QUESTION,
        )

    with chat_tab:
        st.write("\n\n".join(session.transcript))

        def clear_text():
            session.transcript.append(f"Candidate: {candidate_text.strip()}")
            session["candidate_text"] = ""

        candidate_text = chat_tab.text_area(
            "Interview Chat",
            height=50,
            key="candidate_text",
            help="Write the candidate text here"
        )

        run_button = st.button("Enter", help="Submit your chat", on_click=clear_text)
        if run_button:
            if not resume_text:
                st.error("Please enter a resume")
            if not question_text:
                st.error("Please enter a question")
            
            prompt_text = utils.inject_inputs(
                question_text, input_keys=["transcript", "resume"], inputs={
                    "transcript": session.transcript,
                    "resume": INITIAL_RESUME,
                }
            ) + "\nInterviewer:"
            print("prompt_text\n\n", prompt_text)

            resp = run_completion(
                oai_client=oai_client,
                prompt_text=prompt_text,
                model=model,  # type: ignore
                stop=stop,
                max_tokens=max_tokens,  # type: ignore
                temperature=temperature,
            )
            completion_text = resp["completion"].strip()
            if completion_text:
                print("Completion Result: \n\n", completion_text)

            session.transcript.append(f"Interviewer: {completion_text}")
            st.experimental_rerun()

        with feedback_tab:
            st.header("Candidate Feedback")
            prompt_text = utils.inject_inputs(
                question_text, input_keys=["transcript", "resume"], inputs={
                    "transcript": session.transcript,
                    "resume": INITIAL_RESUME,
                }
            )
            feedback_prompt_text = prompt_text + "\n\n" + FEEDBACK_PROMPT
            if st.button("Generate Feedback"):
                resp = run_completion(
                    oai_client=oai_client,
                    prompt_text=feedback_prompt_text,
                    model=model,  # type: ignore
                    stop=stop,
                    max_tokens=400,  # type: ignore
                    temperature=temperature,
                    best_of=3,
                )
                st.write(resp["completion"])


if __name__ == "__main__":
    main()
