import streamlit as st
from dsa_graph import graph, State # Import your compiled app and state
import json

st.title("🤖 DSA Self-Help Platform")

# Initialize session state to store the graph's state
if "graph_state" not in st.session_state:
    st.session_state.graph_state = None

# --- User Input Section ---
topic_input = st.text_input("What DSA topic would you like to practice?", key="topic_input")

if st.button("Generate Question"):
    if topic_input:
        with st.spinner("Researching and generating question..."):
            # This is the initial call to the graph
            initial_state = {"topic": topic_input}
            # The graph will run until it hits the interrupt_before="human_review"
            st.session_state.graph_state = graph.invoke(initial_state)

# --- Human Review Section ---
# This section only appears after the graph has paused for review
if st.session_state.graph_state and "question" in st.session_state.graph_state:
    
    question = st.session_state.graph_state['question']
    st.header(question['title'])
    st.markdown(question['description'])
    st.code(json.dumps(question['test_cases'], indent=2), language='json')

    st.markdown("---")
    st.subheader("Feedback")

    feedback = st.radio("Is this question good enough?", ("Yes", "No"))
    reason = ""
    if feedback == "No":
        reason = st.text_input("What was wrong with the question? (e.g., 'too easy')")

    if st.button("Submit Feedback"):
        with st.spinner("Processing feedback..."):
            # Prepare the feedback to resume the graph
            resume_state = {
                "human_feedback": feedback.lower(),
                "user_comments": reason
            }
            # RESUME the graph execution with the new state information
            final_state = graph.invoke(st.session_state.graph_state, {"messages": [("user", resume_state)]})

            # Update the state with the final result
            st.session_state.graph_state = final_state

# --- Solution Display Section ---
# This section appears only when the graph has finished (i.e., 'solution' exists)
if st.session_state.graph_state and st.session_state.graph_state.get('solution'):
    st.markdown("---")
    st.header("✅ Solution")
    solution = st.session_state.graph_state['solution']
    st.markdown(f"**Thought Process:** {solution}")
    