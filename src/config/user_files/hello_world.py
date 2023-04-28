from pyop import col, did, nid, cid

# Since this is running in a background op, don't use the Anki GUI
print(f'Hello world, I was called with col: {col}, did: {did}, nid: {nid} and cid: {cid}!')

