
import logging
from typing import List
import os
from grpc_tools import protoc

def compile_proto_to_python(proto_file: str,
                  source_dir: str = '.', target_dir: str = '.',
                  include_dirs: List[str] = None, auto_include_library: bool = True, import_local: bool = False) \
        -> bool:

    if include_dirs is None:
        include_dirs = []

    if auto_include_library:
        # add the path the the SilaFramework.proto path as well as the SiLABinaryTransfer.proto
        include_dirs.append(os.path.join(os.path.dirname(__file__), '..', 'framework', 'protobuf'))

    # Construct the command
    #   The main program
    command = ['grpc_tools.protoc']
    #   All import paths
    for path in include_dirs:
        command.append('--proto_path={proto_path}'.format(proto_path=path))
    #   The source path
    command.append('--proto_path={proto_path}'.format(proto_path=source_dir))
    #   The target path(s)
    command.append('--python_out={output_dir}'.format(output_dir=target_dir))
    command.append('--grpc_python_out={output_dir}'.format(output_dir=target_dir))
    #   The proto file
    command.append(proto_file)

    if protoc.main(command) != 0:
        logging.error(
            'Failed to compile .proto code for from file "{proto_file}" using the command `{command}`'.format(
                proto_file=proto_file,
                command=command
            )
        )
        return False
    else:
        logging.info(
            'Successfully compiled "{proto_file}"'.format(
                proto_file=proto_file
            )
        )

    # correct the SiLAFramework import
    #   we use absolute imports here, to allow to copy the stubs out of the library and still keep the dependency on
    #   the SiLAFramework alive
    (pb2_files, _) = os.path.splitext(os.path.basename(proto_file))
    pb2_file = pb2_files + '_pb2.py'
    pb2_grpc_file = pb2_files + '_pb2_grpc.py'
    pb2_file = os.path.join(target_dir, pb2_file)
    pb2_grpc_file = os.path.join(target_dir, pb2_grpc_file)
    with open(pb2_file, 'r', encoding='utf-8') as file_in:
        logging.debug('Correcting {file}'.format(file=pb2_file))
        logging.debug('\t' 'Correcting for import of SiLAFramework')
        replaced_text = file_in.read()
        if import_local:
            replaced_text = replaced_text.replace('import SiLAFramework_pb2',
                                                  'from . import SiLAFramework_pb2')
        else:
            replaced_text = replaced_text.replace('import SiLAFramework_pb2',
                                                  'import sila2lib.framework.SiLAFramework_pb2')
    with open(pb2_file, 'w', encoding='utf-8') as file_out:
        file_out.write(replaced_text)

    with open(pb2_grpc_file, 'r', encoding='utf-8') as file_in:
        logging.debug('Correcting {file}'.format(file=pb2_grpc_file))
        logging.debug('\t' 'Correcting for import of SiLAFramework')
        replaced_text = file_in.read()
        if import_local:
            replaced_text = replaced_text.replace('import SiLAFramework_pb2',
                                                  'from . import SiLAFramework_pb2')
            replaced_text = replaced_text.replace('import SiLABinaryTransfer_pb2',
                                                  'from . import SiLABinaryTransfer_pb2')
        else:
            replaced_text = replaced_text.replace('import SiLAFramework_pb2',
                                                  'import sila2lib.framework.SiLAFramework_pb2')
            replaced_text = replaced_text.replace('import SiLABinaryTransfer_pb2',
                                                  'import sila2lib.framework.SiLABinaryTransfer_pb2')
    with open(pb2_grpc_file, 'w', encoding='utf-8') as file_out:
        file_out.write(replaced_text)

    return True

def compile_proto_to_javascript(proto_file: str,
                  source_dir: str = '.', target_dir: str = '.',
                  include_dirs: List[str] = None, auto_include_library: bool = True, import_local: bool = False) \
        -> bool:

    try :
        protoc_version_output = run_with_return('protoc', ['--version'])
        logging.debug(f"protoc version installed on this system: {protoc_version_output}")
        protoc_version = protoc_version_output.split()[1]
        protoc_ver_maj, protoc_ver_min, protoc_ver_rel = protoc_version.split('.')

        logging.debug(f"protoc maj-version: {protoc_ver_maj} min-ver: {protoc_ver_min} rel-ver: {protoc_ver_rel}  ")

        if  int(protoc_ver_maj) <= 3 and int(protoc_ver_min) < 6:
            logging.warning("JavaScript output only works with protoc >= 3.6.1.\n you have v{protoc_version} installed on your system!" )
            return False

    except Exception as err:
        logging.error(f"({err}): protobuf compiler protoc not installed.")
        return False

    if include_dirs is None:
        include_dirs = []

    if auto_include_library:
        # add the path the the SilaFramework.proto path as well as the SiLABinaryTransfer.proto
        include_dirs.append(os.path.join(os.path.dirname(__file__), '..', 'framework', 'protobuf'))

    # Construct the command parameters
    #   The main program
    command_params = []
    #   All import paths
    for path in include_dirs:
        command_params.append('--proto_path={proto_path}'.format(proto_path=path))
    #   The source path
    command_params.append('--proto_path={proto_path}'.format(proto_path=source_dir))
    #   The target path(s)
    command_params.append('--js_out=import_style=commonjs:{output_dir}'.format(output_dir=target_dir))
    command_params.append('--grpc-web_out=import_style=commonjs,mode=grpcwebtext:{output_dir}'.format(output_dir=target_dir))
    #   The proto file
    command_params.append(proto_file)

    # protoc -I="protos" echo.proto --js_out=import_style=commonjs:generated --grpc-web_out=import_style=commonjs,mode=grpcwebtext:generated
    run_with_return('protoc', command_params )

    logging.info(f"Tried to compile proto-file  [{proto_file}] to javascript.")

    return True
