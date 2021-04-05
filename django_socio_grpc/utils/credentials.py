"""
load_credential utils
"""


def load_credential_from_file(filepath):
    with open(filepath, 'rb') as f:
        return f.read()


def load_credential_from_args(args):
    """load credential from command

    Args:
        args(str): str join `,`

    Returns:
        list of credential content
    """
    if ',' not in args:
        raise
    file_path_list = args.split(',')
    if len(file_path_list) != 2:
        raise
    if not file_path_list[0].endswith('.key'):
        file_path_list[0], file_path_list[1] = file_path_list[1], file_path_list[0]
    return [load_credential_from_file(file_path) for file_path in file_path_list]
