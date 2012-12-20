$(document).ready(function(){
	var rowID;
	rowID = 0;

    $("#add_organism").click(function(e){ 
    	//sets the textbox value for use in the tryCommand function
    	var organism_id = $('#organism_id');
    	var common_name = $('#common_name');
		var htmlData = "<p><label for='id_course_details-" + rowID +"-organism'>Organism:</label><select name='course_details-" + rowID + "-organism' id='id_course_details-" + rowID + "-organism'><option value='" + organism_id + "'>" + common_name + "</option></select><label for='id_course_details-" + rowID + "-DELETE'>Delete:</label><input type='checkbox' name='course_details-" + rowID + "-DELETE' id='id_course_details-" + rowID + "-DELETE' /><input type='hidden' name='course_details-" + rowID + "-course' id='id_course_details-" + rowID + "-course' />";
        $('#organism_list').append(htmlData);
		rowID = rowID + 1;
		//stops the form from refreshing the page like it normally would.
		e.preventDefault();
    }); 

    var textBox = $('#selector');    
	var code = null;
	textBox.keypress(function(e)
	{
		code = (e.keyCode ? e.keyCode : e.which);
		//I think this is "if you press enter"
		if (code == 13) {
			//sets the textbox value for use in the tryCommand function
			var organism_id = $('#organism_id');
	    	var common_name = $('#common_name');
			var htmlData = "<p><label for='id_course_details-" + rowID +"-organism'>Organism:</label><select name='course_details-" + rowID + "-organism' id='id_course_details-" + rowID + "-organism'><option value='" + organism_id + "'>" + common_name + "</option></select><label for='id_course_details-" + rowID + "-DELETE'>Delete:</label><input type='checkbox' name='course_details-" + rowID + "-DELETE' id='id_course_details-" + rowID + "-DELETE' /><input type='hidden' name='course_details-" + rowID + "-course' id='id_course_details-" + rowID + "-course' />";
            $('#organism_list').append(htmlData);
			rowID = rowID + 1;
			e.preventDefault();
		}
	});
});