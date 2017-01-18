**************************************************************Combed_violations.py**************************************************************

*Syntax:

combed_violations.py [-h] (-all | -list LIST) [-path PATH]
-h, --	  	help  show this help message and exit
 -all:        	test all cells
 -list LIST  	test for provided list
 -path PATH  	Review folder path

*Example: Test in the Review folder:

combed_violations.py -all OR combed_violations.py -list  my_list
The script looks for a "cells" folder in the current path and tests all folders inside said folder, excluding flops, latches, CK cells, and fillers.
If instead of -all, the switch "-list" was activated the script would try to read the file specified after the switch, "my_list" in this case in the run folder.
The script would then continue in the same manner as before.

*Example: Test outside the review folder:

./combed_violations.py -all -path /slowfs/us01dwt2p358/proj_lp_ts07dstddre/Review_GE/
If the optional "-path" was activated, then the script would expect a full review folder path and will test the "cells" folder found inside it. 
Next, the script prints the number of cells to be tested (without the flops, latches, CK gates and fillers) and performs a test to determine whether the circuit has a combed architecture.
Finally, it would test for alignment with the name and print a list of failed cells with a description of the error. And In the case of an announced structure, a list of the combed transistors would also be given.
