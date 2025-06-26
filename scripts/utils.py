import json
import logging


def llm_chat(ollama_client, model_name,system_mesage, prompt):
    """
    Function to generate a description using the Ollama model.
    """
    chat_completion = ollama_client.chat(
        model=model_name,
        messages=[
            {"role": "system", "content": system_mesage},
            {"role": "user", "content": prompt}
        ],
        options={"temperature": 0}
    )
    return chat_completion['message']['content']


def get_supp_codes(tidy_supp_data, code, taxon_name):
    """
    Function to get the code and value from the tidy supplementary data
    for a specific taxon name.
    """
    return tidy_supp_data[
        (tidy_supp_data.code == code) &
        (tidy_supp_data.taxon_name == taxon_name)
    ][["code", "value"]].to_json(orient='records')


def append_output(output_list, taxon_name, output, subject):
    """
    Appends a dictionary with taxon_name, output_sentence, and subject to the output_list.
    """
    loop_dict = {
        "taxon_name": taxon_name,
        "output_sentence": output,
        "subject": subject
    }
    output_list.append(loop_dict)


def check_valid_json(output, taxon_dict):
    try:
        sentence_dict = json.loads(output)
        taxon_dict.update(sentence_dict)
    except Exception as e:
        logging.error(f"Failed to parse JSON {output} | Error: {e}")
    return taxon_dict