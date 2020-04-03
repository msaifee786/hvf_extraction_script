###############################################################################
# hvf_ui_launcher.py
#
# Description:
#	Launches UI frame for specific UI classes
#
#
#
###############################################################################

# Import necessary packages
from includes.ui_modules.ui_hvf_viewer import Ui_Hvf_Viewer;

# Construct the argument parse and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-u", "--ui", required=False,
	help="UI class to launch")


# Set up the logger module:
#debug_level = Logger.DEBUG_FLAG_INFO;
debug_level = Logger.DEBUG_FLAG_WARNING;
#debug_level = Logger.DEBUG_FLAG_DEBUG;
msg_logger = Logger.get_logger().set_logger_level(debug_level);


###############################################################################
# UI HVF Viewer ###############################################################
###############################################################################

# If we are passed in an image, read it and show results
if (args["ui"] == "ui_hvf_viewer"):

	app = Ui_Hvf_Viewer()
	app.master.title('HVF Viewer');
	app.mainloop();

else:
	Logger.get_logger().log_msg(Logger.DEBUG_FLAG_SYSTEM, "Incorrect argument")
