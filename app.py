import streamlit as st
from dsa_graph import graph, State # Import your compiled app and state
import json
# Make sure to import your Pydantic models to access their attributes
from question_generator import CodeQuestion, TestCase 

st.title("🤖 DSA Self-Help Platform")

# Initialize session state to store the graph's state and other UI flags
if "graph_state" not in st.session_state:
    st.session_state.graph_state = None

# --- User Input Section ---
topic_input = st.text_input("What DSA topic would you like to practice?", key="topic_input")

if st.button("Generate Question"):
    if topic_input:
        with st.spinner("Researching and generating question..."):
            initial_state = {"topic": topic_input}
            # The graph will run until it hits the interrupt_before="human_review"
            st.session_state.graph_state = graph.invoke(initial_state)

# Determine if the graph is paused for review OR has finished
is_paused_for_review = st.session_state.graph_state and "question" in st.session_state.graph_state and not st.session_state.graph_state.get("solution")
is_finished = st.session_state.graph_state and st.session_state.graph_state.get("solution")

# --- Human Review Section ---
if is_paused_for_review:
    question_dict = st.session_state.graph_state['question']
    st.header(question_dict['title'])
    st.markdown(question_dict['description'])
    # Assuming test_cases is a list of Pydantic objects, convert to dict for display
    test_cases_dict = [tc for tc in question_dict.get('test_cases', [])]
    st.code(json.dumps(test_cases_dict, indent=2), language='json')

    st.markdown("---")
    st.subheader("Feedback")

    feedback = st.radio("Is this question good enough?", ("Yes", "No"), key="feedback_radio")
    reason = ""
    if feedback == "No":
        reason = st.text_input("What was wrong with the question? (e.g., 'too easy')", key="reason_input")

    if st.button("Submit Feedback"):
        with st.spinner("Processing feedback..."):
            # FIX 1: Get the current paused state
            current_state = st.session_state.graph_state
            
            # FIX 2: Add user's feedback directly to the state with the correct keys
            current_state['human_feedback'] = feedback.lower()
            current_state['user_comments'] = reason
            
            # FIX 3: Resume the graph with the UPDATED state
            final_state = graph.invoke(current_state , start_at="Question Generator")
            
            # Update the session state with the new result
            st.session_state.graph_state = final_state
            # Rerun the script to immediately show the solution or the regenerated question
            st.rerun()

# --- Solution Display Section ---
elif is_finished:
    # Display the final question again for context
    question_dict = st.session_state.graph_state['question']
    st.header(question_dict['title'])
    st.markdown(question_dict['description'])

    st.markdown("---")
    st.header("✅ Solution")
    
    # FIX 4: Access the attributes of the solution dictionary correctly
    solution_dict = st.session_state.graph_state['solution']
    st.markdown(f"**Thought Process:**\n{solution_dict.get('thought_process', 'N/A')}")
    st.markdown(f"**Complexity Analysis:**\n{solution_dict.get('complexity_analysis', 'N/A')}")
    st.code(solution_dict.get('code', '# No code provided'), language="python")