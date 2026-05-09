Create a Prime Intellect Environment designed to evaluate how well a model teaches a subject. Import a dataset containing information regarding the topic we would like to explore. 
<!-- 
Practice Questions - these can be drawn from resources in multiple different ways -->

Dataset
- Currently a physics/chemistry dataset imported from "xw27/scibench" containing questions and as well as a numerical answer
- Attributes
    - "question" - A provided question intended for the teacher model to teach
    - "answer" - The answer to the provided question under "question"
    - "test_question" - A test question intended to evaluate the student model's understanding
    - "test_answer" - The answer to the provided question under "test_question"
    - "required_information" - Any formulas, context, vocabulary that the teacher model must mention
- Derived from lecture slides, textbook page, lecture transcript

- No Labelled Data - Much more convenient for customers to immediately run evaluations, evaluation results from structure of the verifier rather than the training data itself

- Confidence levels


Algorithms
- Knowledge Graph
- Source fidelity
- Readability
- Information Density
- Coherence



Verifiers
- Construct a Rubric Group consisting of two rubric types
    - Deterministic Rubric - Deterministically evaluate whether or not the model's output matches the ground truth. Furthermore perform an f1 analysis based on whether or not the teacher model mentions the required information
    - F1 grading for consise/clarity

    - Algorithms to deterministically evaluate teaching
        - Ground truth knowledge graph
            - Nodes: concepts, edges - prequisite relationships
            - Order score - introducing concepts in chronological order
            - Embedding similarity - how many sentences discuss the topic
        - With detailed data labelling
            - 1. Prerequisite order score
            - 2. Concept Converge
            - 3. Explanation depth per concept
        - textstat for evaluating tone, grade_level, 

    - Modes
        - Text
        - Image Generation
            - Cosine Similarity

System Prompt for smaller model: 
You are a student struggling with [Topic]. Do not use outside knowledge. Only learn from what the teacher tells you."

Learning delta - test the student before and after, improvements lead to a larger reward

Step checklist - make sure that the steps are sound

Multi-turn Environment
- We want to construct a multi-turn environment in which the model retries until a stop condition is resolved
- Stop Condition
    - Either max_turns = 10 
    - The user has learned the content - when the student says that they understand the content
        - If the student says that they understand the content, the teacher model should assign the same exact question fo the student to do except with different numerical values
            - If the student fails set student_understands to false
            - If the student succeeds set student_understanding_verified to true and stop

<!-- Ideas
- Data could be documents/slideshows instead of basic questions
    - Students would come up with questions/answers through data labelling
- How do we evaluate the AI's capability to teach? -->