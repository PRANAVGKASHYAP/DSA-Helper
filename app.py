import streamlit as st
import json
from dsa_graph import graph  # import your compiled graph
import langgraph

st.set_page_config(page_title="DSA Self-Help Platform", layout="wide")
st.title("🤖 DSA Self-Help Platform")

# ---- Session State Initialization ----
if "graph_state" not in st.session_state:
    st.session_state.graph_state = None
if "paused" not in st.session_state:
    st.session_state.paused = False

# ---- User Input ----
topic_input = st.text_input("What DSA topic would you like to practice?", key="topic_input")

if st.button("Generate Question"):
    if topic_input.strip():
        with st.spinner("Researching and generating question..."):
            initial_state = {"topic": topic_input.strip()}
            # Run until interruption after Question Generator
            result = graph.invoke(initial_state)
            st.session_state.graph_state = result
            st.session_state.paused = True
            st.rerun()

# ---- Paused State (Question Review) ----
if st.session_state.paused and st.session_state.graph_state:
    question_dict = st.session_state.graph_state["question"]

    st.header(question_dict.get("title", "Untitled Question"))
    st.markdown(question_dict.get("description", ""))

    # Show test cases if available
    if "test_cases" in question_dict:
        st.subheader("Test Cases")
        st.code(json.dumps(question_dict["test_cases"], indent=2), language="json")

    st.markdown("---")
    st.subheader("Feedback")

    feedback = st.radio("Is this question good enough?", ("Yes", "No"), key="feedback_radio")
    reason = ""
    if feedback == "No":
        reason = st.text_area("Please describe what was wrong with the question", key="reason_input")

    if st.button("Submit Feedback"):
        if st.session_state.graph_state:
            with st.spinner("Processing feedback..."):

                # 1️⃣ Get the current paused state
                current_state = st.session_state.graph_state

                # 3️⃣ Resume the graph from the last paused node
                final_state = graph.invoke(
                    current_state, 
                    start_at="Question Generator"  # continue from where we left off
                )

                # 4️⃣ Update the session state
                st.session_state.graph_state = final_state
                st.session_state.paused = False

                # 5️⃣ Rerun to reflect the new state
                st.rerun()


# ---- Finished State (Solution Ready) ----
if st.session_state.graph_state and st.session_state.graph_state.get("solution"):
    question_dict = st.session_state.graph_state["question"]
    solution_dict = st.session_state.graph_state["solution"]

    st.header(question_dict.get("title", "Final Question"))
    st.markdown(question_dict.get("description", ""))

    st.markdown("---")
    st.header("✅ Solution")
    st.markdown(f"**Thought Process:**\n{solution_dict.get('thought_process', 'N/A')}")
    st.markdown(f"**Complexity Analysis:**\n{solution_dict.get('complexity_analysis', 'N/A')}")
    st.code(solution_dict.get("code", "# No code generated"), language="python")

    if st.button("🔄 Try Another Question"):
        st.session_state.graph_state = None
        st.session_state.paused = False
        st.rerun()
