import sys
sys.path.append(r'C:\\Users\\MY PC\\OneDrive\\Desktop\\assessment\\kg_demo')
try:
    import backend.main
    print('Import OK')
except Exception as e:
    import traceback
    traceback.print_exc()
    raise
