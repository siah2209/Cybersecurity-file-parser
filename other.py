
"""

from stegano import lsb

# Original image must be PNG (use a clean image)
input_image = "testphoto.png"
output_image = "hidden_message_image.png"
secret_message = "The doctor prescribed me oxycodone for pain. I picked up some oxycodone from the trap house. Picked up some perks after surgery from the pharmacy. Selling perks on the block, 10 a pop."


# Encode
lsb.hide(input_image, secret_message).save(output_image)
print(f"✅ Stego message saved in {output_image}")
"""

import os

folder = "C:\\Users\\c2m3j\\OneDrive\\Documents\\test2"

print("Path exists:", os.path.exists(folder))

if os.path.exists(folder):
    print("Files in folder:")
    print(os.listdir(folder))
else:
    print("❌ Folder not found")
