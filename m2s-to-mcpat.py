import sys
import re

# regexp to find the title of a section, like "[ Config.General ]"
section_title_regex = re.compile( r"\s*\[ ([^\s\]]+) \]\s*" )

# regexp to find each component ID of the mcpat template, like "<component id="system.core0""
component_id_regex = re.compile( r"\s*<component id=\"([^\s\"]+)\"\s*" )

# regexp to find each stat name contained within a component
stat_name_regex = re.compile( r"\s*<stat name=\"([^\s\"]+)\"\s*" )

# global variable to keep track of what section are we parsing now
current_section = None

# global variable to keep track of what component are we filling now
current_component = None

# correspondences between McPat and Multi2Sim (A.K.A. m2s) statistics
# all parameters in the left column of this list will be tried to be
# replaced in the mcpat template for their equivalent parameters in m2s (right column)
# MODIFY THIS LIST IN ORDER TO ADAPT THIS PROGRAM TO YOUR OWN NEEDS
corresp_mcpat_to_m2s = {
    "system->total_cycles":                            "Global->Cycles",
    "system->busy_cycles":                             "Global->Cycles",
    "system.core0->total_instructions":                "c0->Dispatch.Total",
    # ("",""),
    # ("",""),
    # ("",""),
}

# The parser is called on every line of the m2sInputFile, and it dynamically creates
# a dictionary where every entry is a section of the m2s file, and every value is
# another dictionary that contains all the parameters and values for that section
def parser( line, m2s_sections ):
    global current_section

    # if we find a section title
    section_title = section_title_regex.match( line )
    if section_title:
        # DEBUG: print section_title.group(1)
        # we create a new pair into the m2s_sections dictionary, where
        # the key is the section title and the value is another dictionary,
        # which will contain all pairs of parameters/values for that section
        m2s_sections[section_title.group(1).strip()] = {}
        current_section = section_title.group(1).strip() # we update the current section name
    # otherwise we are still inside a section
    else:
        try:
            # this will fail if there's no pair of "param = value" in the line
            param_name, param_value = line.split("=")
        except ValueError:
            pass
        else:
            # DEBUG: print param_name.strip(), param_value.strip()
            if current_section is not None:
                # we define a new entry where the key is the name of the parameter, and we also assign its value
                m2s_sections[current_section][param_name.strip()] = param_value.strip()

# The filler is called on every line of the mcpatTemplateFile. If the line doesn't contain a
# parameter from corresp_mcpat_to_m2s that needs to be filled with its corresponding value from m2s, it is
# simply copied from mcpatTemplateFile to mcpatOutputFile, otherwise its value is obtained from m2s_sections
def filler( line, mcpatOutputFile, m2s_sections):
    global current_component

    # if we find a parameter and is in the list of corresp_mcpat_to_m2s it means we have to fill its value
    stat_name = stat_name_regex.match( line )
    if (stat_name) and (current_component+"->"+stat_name.group(1) in corresp_mcpat_to_m2s): # TODO: this expression might be wrong
        #print "DEBUG: stat",stat_name.group(1),"found in correspondences list"
        m2s_correspondence = corresp_mcpat_to_m2s[current_component+"->"+stat_name.group(1)]
        m2s_correspondence_section, m2s_correspondence_parameter = m2s_correspondence.split("->")
        try:
            param_value = m2s_sections[m2s_correspondence_section][m2s_correspondence_parameter]
        except KeyError:
            print "ERROR: corresponding stat not found in m2s dictionary"
        else:
            mcpatOutputFile.write("<stat name=\""+stat_name.group(1)+"\" value=\""+param_value+"\"/>\n")
            print "DEBUG: stat",stat_name.group(1)+"="+param_value,"successfully filled"
    else:
        # if we find a component
        component_id = component_id_regex.match( line )
        if component_id:
            current_component = component_id.group(1) # we update the current component ID
            print "DEBUG: component",current_component,"found in template"
        # else:
        #     print "DEBUG: this line is not a component nor a recognized stat", line
        # if the parameter is not in the list, or if the line refers to a component, or it refers to something else,
        # we just copy the line verbatim
        mcpatOutputFile.write(line)


if __name__ == '__main__': #this is how the main function is called in python
    # Command to execute this code: shell> python m2s-to-mcpat.py <m2sInputFile> <mcpatTemplateFile.xml> <mcpatOutputFile.xml>
    # This program takes a Multi2Sim results file, it reads the components it needs for McPat, it makes a copy of the mcpat template file
    # and it overwrites that copy with the components indicated. The template file should have the structure of each component and the list
    # of parameters that we're trying to copy from m2s. If any of the components is not found on the template (mcpatTemplateFile), the parsing will fail.

    m2sInputFileName = sys.argv[1] # first argument is the m2s results output file from where we'll read the values
    mcpatTemplateFileName = sys.argv[2] # second argument is the mcpat template that we're trying to fill (this file won't be modified)
    mcpatOutputFileName = sys.argv[3] # third argument is the actual output file, ready to be used as input XML in mcpat

    m2s_sections = {} # this dictionary will contain one row per every section in the m2s results file

    # we read and parse m2sInputFile one line at a time (this will automatically close the file at the end)
    with open(m2sInputFileName) as m2sInputFile:
        for line in m2sInputFile:
            parser(line, m2s_sections)

    mcpatOutputFile = open(mcpatOutputFileName,"w") # we create the resulting output file name

    # we read and parse m2sInputFile one line at a time (this will automatically close the file at the end)
    with open(mcpatTemplateFileName) as mcpatTemplateFile:
        for line in mcpatTemplateFile:
            filler(line, mcpatOutputFile, m2s_sections)

    mcpatOutputFile.close() # once we've finished reading all the mcpatTemplateFile, we close the output file and we're done.
