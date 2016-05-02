__author__ = 'nherbaut'
import os



def get_transcoded_file(context,bitrate):
    return os.path.join(get_transcoded_folder(context), str(bitrate) + ".h264")

def get_yuv_file(context):
    return os.path.join(get_transcoded_folder(context),"decoded_file.yuv")


def get_transcoded_folder(context):
    return os.path.join(context["folder_out"], "encoding")

def get_description_folder(context):
    return os.path.join(context["folder_out"], "create_description")

def get_plus_description_folder(context):
    return os.path.join(context["folder_out"],"create_plus_description")

def get_mp4_description_folder(context,number):
	return os.path.join(context["folder_out"],"description_"+str(number))

def get_plus_mp4_description_folder(context,number):
 	return os.path.join(context["folder_out"],"description_plus_"+str(number))

def get_plus_dash_folder(context,number):
    return os.path.join(context["folder_out"], "dash_description_plus_"+str(number))

def get_dash_folder(context,number):
    return os.path.join(context["folder_out"], "dash_description_"+str(number))

def get_description_zip_folder(context,number):
    return os.path.join(context["folder_out"], "zip_dash_description_"+context["videoID"]+"_"+str(number)+".zip")

def get_description_plus_zip_folder(context,number):
    return os.path.join(context["folder_out"], "zip_plus_dash_description_"+context["videoID"]+"_"+str(number)+".zip")

def get_mpd_zip_folder(context):
    return os.path.join(context["folder_out"],context["videoID"]+".zip")

def get_dash_mpd_file_folder(context):
    return os.path.join(context["folder_out"],"mpd_folder")

def get_dash_mpd_file_path(context,number):
    return os.path.join(get_dash_folder(context,number), str(number) + ".mpd")

def get_plus_dash_mpd_file_path(context,number):
    return os.path.join(get_plus_dash_folder(context,number), "plus_"+str(number) + ".mpd")

# Need to be modified
def get_postProcessor_path(context):
    return os.path.abspath("adaptation/MD-openh264/postProcessor ")

# Need to be modified
def get_welsenc_path(context):
    return os.path.join(os.path.abspath("adaptation/openh264-projetS8/h264enc ") + os.path.abspath("adaptation/openh264-projetS8/mytests/welsenc.cfg"))

# Need to be modified
def get_layer_path(context):
    return os.path.abspath("adaptation/openh264-projetS8/mytests/layer2.cfg")

def get_dim_as_str(context):
    return str(context["target_width"]) + "x" + str(context["target_height"])


pass
