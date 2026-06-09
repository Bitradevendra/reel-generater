import traceback, os, sys

# Redirect stderr to capture llama.cpp verbose output
log_file = open('_test_output.txt', 'w', encoding='utf-8')

try:
    from llama_cpp import Llama
    log_file.write('llama-cpp-python imported OK\n')
    
    model_path = os.path.abspath('script/model.gguf')
    log_file.write(f'Model path: {model_path}\n')
    log_file.write(f'Exists: {os.path.exists(model_path)}\n')
    log_file.write(f'Size: {os.path.getsize(model_path) / 1024**3:.2f} GB\n')
    
    llm = Llama(
        model_path=model_path,
        n_ctx=512,
        n_threads=4,
        n_gpu_layers=0,
        verbose=False,
    )
    log_file.write('Model loaded successfully!\n')
    
    out = llm('Say hello.', max_tokens=10, echo=False)
    log_file.write(f'Output: {out["choices"][0]["text"][:200]}\n')
    log_file.write('SUCCESS!\n')
    
except Exception as e:
    log_file.write(f'ERROR: {type(e).__name__}: {e}\n')
    traceback.print_exc(file=log_file)

log_file.close()
# Print results
with open('_test_output.txt', 'r') as f:
    print(f.read())
