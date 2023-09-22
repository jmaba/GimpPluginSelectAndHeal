import gimpcolor
from gimpfu import *
import sys
import os

debug = False

def foo(color_image_path,mask_image_path, outputFile):
    color_image = pdb.file_jpeg_load(color_image_path, color_image_path)
    mask=pdb.gimp_file_load_layer(color_image,mask_image_path)
    pdb.gimp_image_add_layer(color_image, mask,0)
    pdb.gimp_image_select_color(color_image, CHANNEL_OP_REPLACE, mask,gimpcolor.RGB(255,255,255))
    timg = color_image
    tdrawable =  pdb.gimp_image_get_active_layer(color_image)
    pdb.gimp_image_remove_layer(timg, tdrawable)
    
    #Copied from python_fu_heal_selection...
    tdrawable =  pdb.gimp_image_get_active_layer(color_image)
    samplingRadiusParam=50
    directionParam=0
    orderParam=0
    
    if pdb.gimp_selection_is_empty(timg):
        pdb.gimp_message(_("You must first select a region to heal."))
        return
      
    pdb.gimp_image_undo_group_start(timg)
      
    targetBounds = tdrawable.mask_bounds

    tempImage = pdb.gimp_image_duplicate(timg)
    if not tempImage:
        raise RuntimeError, "Failed duplicate image"
      
    # !!! The drawable can be a mask (grayscale channel), don't restrict to layer.
    work_drawable = pdb.gimp_image_get_active_drawable(tempImage)
    if not work_drawable:
        raise RuntimeError, "Failed get active drawable"
          
      
    orgSelection = pdb.gimp_selection_save(tempImage) # save for later use
    pdb.gimp_selection_grow(tempImage, samplingRadiusParam)
      
    grownSelection = pdb.gimp_selection_save(tempImage)
      
    pdb.gimp_selection_combine(orgSelection, CHANNEL_OP_SUBTRACT)
      
      
    frisketBounds = grownSelection.mask_bounds
    frisketLowerLeftX = frisketBounds[0]
    frisketLowerLeftY = frisketBounds[1]
    frisketUpperRightX = frisketBounds[2]
    frisketUpperRightY = frisketBounds[3]
    targetLowerLeftX = targetBounds[0]
    targetLowerLeftY = targetBounds[1]
    targetUpperRightX = targetBounds[2]
    targetUpperRightY = targetBounds[3]
      
    frisketWidth = frisketUpperRightX - frisketLowerLeftX
    frisketHeight = frisketUpperRightY - frisketLowerLeftY
      
    # User's choice of direction affects the corpus shape, and is also passed to resynthesizer plugin
    if directionParam == 0: # all around
      # Crop to the entire frisket
      newWidth, newHeight, newLLX, newLLY = ( frisketWidth, frisketHeight, 
        frisketLowerLeftX, frisketLowerLeftY )
    elif directionParam == 1: # sides
      # Crop to target height and frisket width:  XTX
      newWidth, newHeight, newLLX, newLLY =  ( frisketWidth, targetUpperRightY-targetLowerLeftY, 
        frisketLowerLeftX, targetLowerLeftY )
    elif directionParam == 2: # above and below
      # X Crop to target width and frisket height
      # T
      # X
      newWidth, newHeight, newLLX, newLLY = ( targetUpperRightX-targetLowerLeftX, frisketHeight, 
        targetLowerLeftX, frisketLowerLeftY )
    # Restrict crop to image size (condition of gimp_image_crop) eg when off edge of image
    newWidth = min(pdb.gimp_image_width(tempImage) - newLLX, newWidth)
    newHeight = min(pdb.gimp_image_height(tempImage) - newLLY, newHeight)
    pdb.gimp_image_crop(tempImage, newWidth, newHeight, newLLX, newLLY)
      
    # Encode two script params into one resynthesizer param.
    # use border 1 means fill target in random order
    # use border 0 is for texture mapping operations, not used by this script
    if not orderParam :
      useBorder = 1   # User wants NO order, ie random filling
    elif orderParam == 1 :  # Inward to corpus.  2,3,4
      useBorder = directionParam+2   # !!! Offset by 2 to get past the original two boolean values
    else:
      # Outward from image center.  
      # 5+0=5 outward concentric
      # 5+1=6 outward from sides
      # 5+2=7 outward above and below
      useBorder = directionParam+5
          

      
      # Note that the API hasn't changed but use_border param now has more values.
    pdb.plug_in_resynthesizer(timg, tdrawable, 0,0, useBorder, work_drawable.ID, -1, -1, 0.0, 0.117, 16, 500)
      
      # Clean up (comment out to debug)
    gimp.delete(tempImage)
    #layer = pdb.gimp_image_merge_visible_layers(timg, CLIP_TO_IMAGE)
    pdb.gimp_file_save(timg, tdrawable, outputFile,'?')
    #gimp.Display(timg) 
    
    pdb.gimp_image_undo_group_end(timg)    

def apply_mask_to_image(color_folder, mask_folder, output_folder):
    #color_image_path = "M:\\test\\1image.jpg"
    #mask_image_path = "M:\\test\\1mask.jpg"
    #foo(color_image_path, mask_image_path)
    color_files = [f for f in os.listdir(color_folder) if os.path.isfile(os.path.join(color_folder, f))]

    mask_files = [f for f in os.listdir(mask_folder) if os.path.isfile(os.path.join(mask_folder, f))]
    
    # Check if both folders have the same number of files
    if len(color_files) != len(mask_files):
        gimp.message("Color and mask folders must contain the same number of files")
        return
    
    # Sort files to match pairs correctly
    color_files.sort()
    mask_files.sort()

    # Create output folder if it doesn't exist
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    for color_file, mask_file in zip(color_files, mask_files):
        color_image_path = os.path.join(color_folder, color_file)
        mask_image_path = os.path.join(mask_folder, mask_file)
        output_image_path = os.path.join(output_folder, color_file)
        output_image_path = os.path.splitext(output_image_path)[0] + "_altered.bmp"
        foo(color_image_path, mask_image_path, output_image_path)

register(
    "apply_mask_and_filter",
    "Apply mask and filter",
    "Apply a mask to a color image and perform additional filtering",
    "Author Name",
    "Author Name",
    "2023",
    "Apply mask and filter",
    "",
    [
        (PF_DIRNAME, "color_folder", "Color Image Folder", None),
        (PF_DIRNAME, "mask_folder", "Mask Image Folder", None),
        (PF_DIRNAME, "output_folder", "Output Folder", None),    ],
    [],
    apply_mask_to_image,
    menu="<Image>/Filters/Enhance"
)

main()
