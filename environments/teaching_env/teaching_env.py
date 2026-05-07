import verifiers as vf
from datasets import Dataset



class TeachingEnv(vf.MultiTurnEnv):
    async def env_response(self, messages: vf.Messages, state: vf.State) -> vf.Message:
        parsed = self.parser.parse(messages)
        action = parsed.action
        feedback = process_action(action)

async def evaluate_content(response, ground_truth):
    pass

async def evaluate_delivery(resposne, ground_truth):
    pass

def load_environment(**kwargs) -> vf.Environment:
    """
    Loads a custom environment.
    """
    
    dataset = Dataset.from_list([
        {"prompt" : [{"role" : "user", "content" : "What is 10 * 10"}], "info" : '{ "type" : "math", "difficulty" : 3}', "answer" : "10"},
        {"prompt" : [{"role" : "user", "content" : "What is 10 * 10"}], "info" : '{ "type" : "math", "difficulty" : 3}', "answer" : "10"}
    ])
    
    rubric = vf.Rubric(funcs=[evaluate_content, evaluate_delivery], weights = [0.5, 0.5])
    return TeachingEnv(dataset = dataset, rubric = rubric, max_turns = 5)


