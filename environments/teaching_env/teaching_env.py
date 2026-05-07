import verifiers as vf
from datasets import Dataset
from datasets import load_dataset



class TeachingEnv(vf.MultiTurnEnv):
    # * How the environment responds after each turn
    async def env_response(self, messages: vf.Messages, state: vf.State) -> vf.Messages:
        if (self.max_turns == 0):
            state["understanding"] = 0
        parsed = self.parser.parse(messages)
        action = parsed.action
        feedback = self.process_action(action)
        return [{"role" : "user", "content" : feedback}]
        
    def process_action(self, action):
        print(action)

async def evaluate_content(completion, prompt, answer, info) -> float:
    
    return 0.0
    

async def evaluate_delivery(completion, prompt, answer, info) -> float:
    response = completion[-1]["content"]
    if info["type"] == "math":
        return 1.0 if answer in response else 0.0
    return 0.0


# * Arbitrary Dataset Builder
def create_dataset(rollouts = 2) -> vf.DatasetBuilder:
    def build() -> Dataset:
        dataset = load_dataset("xw27/scibench", split = 'train') \
                        .rename_columns({'problem_text' : 'question', 'answer_number' : 'answer'}) \
                        .select_columns(["question", "answer"]) \
                        .select(range(rollouts))
                        
        required_formulas = [
            """
            PV = nRT
            """,
            """
            """
        ]
        
        test_questions = [
                """
                Suppose that $52.0 \\mathrm{~mol} \\mathrm{C}_2 
                \\mathrm{H}_6(\\mathrm{~g})$ is confined to $3.150 
                \\mathrm{dm}^3$ at $47^{\\circ} \\mathrm{C}$. 
                Predict the pressure exerted by the ethane 
                from the perfect gas.
                """,
                """
                Assume all gases are perfect unless stated otherwise. 
                Unless otherwise stated, thermodynamic data are for 
                298.15 K. Calculate the standard enthalpy of solution 
                of $\\mathrm{AgBr}(\\mathrm{s})$ in water from the 
                enthalpies of formation of the solid and the aqueous ions.
                """
        ]
        
        test_answers = [
            "43.8",
            "+84.40"
        ]
        
        dataset.add_column("test_questions", test_questions)
        dataset.add_column("test_answers", test_answers)
        dataset.add_column("required_information", required_formulas)
        return dataset
    
    return build


def load_environment(**kwargs) -> vf.Environment:
    """
    Loads a custom environment.
    """
    build_dataset = create_dataset(rollouts=2)
    judge_rubric = vf.JudgeRubric(
        judge_model = "gpt-4.1-mini",
        judge_prompt = """Rate this quality of instruction from 0-10.
        Response: {response}
        Score:"""
    )
    deterministic_rubric = vf.Rubric(funcs=[evaluate_content], weights = [0.5, 0.5])
    rubric = vf.RubricGroup([deterministic_rubric, judge_rubric])
    return TeachingEnv(dataset = build_dataset, rubric = rubric, max_turns = 10)


