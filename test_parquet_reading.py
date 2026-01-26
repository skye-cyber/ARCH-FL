#!/usr/bin/env python3

import os
import pandas as pd
import pyarrow.parquet as pq

print("🔍 Testing parquet file reading...")

try:
    # Check if files exist
    parquet_files = [
        "src/datasets/mimic_cxr/data/train-00000-of-00002.parquet",
        "src/datasets/mimic_cxr/data/train-00001-of-00002.parquet"
    ]
    
    for file in parquet_files:
        if os.path.exists(file):
            print(f"✅ File exists: {file}")
            file_size = os.path.getsize(file)
            print(f"📏 File size: {file_size / (1024*1024):.2f} MB")
        else:
            print(f"❌ File not found: {file}")
    
    # Try reading just the schema first (lightweight)
    print("\n📋 Reading schema from first file...")
    schema = pq.read_schema(parquet_files[0])
    print(f"✅ Schema: {schema}")
    
    # Try reading just a small sample
    print("\n🔍 Reading first 5 rows...")
    table = pq.read_table(parquet_files[0], nthreads=1)
    df_sample = table.to_pandas().head(5)
    print(f"✅ Sample data:\n{df_sample}")
    
    print(f"\n📊 Columns: {list(df_sample.columns)}")
    
    # Check image column
    if 'image' in df_sample.columns:
        print(f"🖼️ Image column type: {type(df_sample['image'].iloc[0])}")
        print(f"🖼️ Image data sample: {df_sample['image'].iloc[0][:100]}...")  # First 100 chars
    
    print("\n🎉 Parquet reading test completed successfully!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()