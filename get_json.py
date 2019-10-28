import json
from config import get_config
from generators import retrieve_generator

if __name__ == "__main__":

    config = get_config()
    tasks = config['tasks']
    jobs = []

    generator = retrieve_generator('stepbystep')()

    with open('stepbystep_input.txt', 'w') as fid:
        buffer = []
        for sample in generator:
            buffer.append(sample)

            if len(buffer) == 3:
                fid.write(json.dumps(buffer))
                fid.write('\n')
                buffer.clear()
