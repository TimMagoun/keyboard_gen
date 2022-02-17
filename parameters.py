

from switch_config import SwitchConfig



class Parameters():

    def __init__(self, parameter_dict: dict = None):
        self.parameter_dict = parameter_dict

        self.default_parameter_dict = {
            'plate_supports': True,
            
            'x_build_size' : 200,
            'y_build_size' : 200,

            'switch_type': 'mx_openable',
            'stabilizer_type': 'cherry',

            'custom_shape': False, 
            'custum_shape_points': None,
            'custom_shape_path': None,

            'kerf' : 0.00,

            'top_margin' : 8,
            'bottom_margin' : 8,
            'left_margin' : 8,
            'right_margin' : 8,
            'case_height' : 10,
            # 'plate_wall_thickness' : 2.0,
            'case_wall_thickness' : 2.0,
            'plate_thickness' : 1.511,
            'plate_corner_radius' : 4,
            'bottom_cover_thickness': 2,

            'support_bar_height' : 3.0,
            'support_bar_width' : 1.0,
            'tilt': 0.0,

            'simple_test': False,

            'screw_count': 8,
            'screw_diameter': 4,
            'screw_edge_inset': 6.5,

            'cable_hole': False,
            'hole_width': 10,
            'hole_height': 10,
            'cable_hole_down_offset': 1
        }


        self.paramater_alternate_dict = {
            'plate_wall_thickness': 'case_wall_thickness'
        }



        self.plate_supports = True
        
        self.x_build_size = 200
        self.y_build_size = 200

        self.switch_type = 'mx_openable'
        self.stabilizer_type = 'cherry'

        self.custom_shape = False 
        self.custum_shape_points = None
        self.custom_shape_path = None

        self.kerf = 0.00

        self.top_margin = 8
        self.bottom_margin = 8
        self.left_margin = 8
        self.right_margin = 8
        self.case_height = 10
        self.case_wall_thickness = 2.0
        self.plate_thickness = 1.511
        self.plate_corner_radius = 4
        self.bottom_cover_thickness = 2

        self.support_bar_height = 3.0
        self.support_bar_width = 1.0
        self.tilt = 0.0

        self.simple_test = False

        self.screw_count = 8
        self.screw_diameter = 4
        self.screw_edge_inset = 6.5
        self.screw_hole_body_wall_width = 2
        self.screw_hole_body_support_x_factor = 4

        self.cable_hole = False
        self.hole_width = 10
        self.hole_height = 10
        self.cable_hole_up_offset = 1
        self.cable_hole_down_offset = 1

        self.switch_config = None

        # self.build_attr_from_dict(self.default_parameter_dict)
        
        if self.parameter_dict is not None:
            self.build_attr_from_dict(self.parameter_dict)

        # self.validate_parameters()
        

    def update_calculated_attributes(self):
        # Calculated attributes
        # self.case_height_base_removed = self.case_height - self.bottom_cover_thickness
        # self.case_height_extra_fill = self.case_height + self.case_height_extra
        # self.side_margin_diff = self.right_margin - self.left_margin
        # self.top_margin_diff = self.bottom_margin - self.top_margin
        # self.screw_tap_hole_diameter = self.screw_diameter - 0.35
        self.screw_hole_body_diameter = self.screw_diameter + (self.screw_hole_body_wall_width * 2)
        self.screw_hole_body_radius = self.screw_hole_body_diameter / 2
        # self.x_screw_width = self.real_case_width - ((self.screw_edge_inset * 2))# + self.screw_diameter)
        # self.y_screw_width = self.real_case_height - ((self.screw_edge_inset * 2))# + self.screw_diameter)
        # self.bottom_section_count = math.ceil(self.real_case_width / self.x_build_size)
        # self.screw_hole_body_support_end_x = (self.case_height_extra_fill / self.screw_hole_body_support_x_factor) + x_offset


    def build_attr_from_dict(self, parameter_dict):
        for param in parameter_dict.keys():
            ignore_deprecated = False
            value = parameter_dict[param]

            # If the current parameter has been deprecated by another parameter get the new parameter name
            if param in self.paramater_alternate_dict.keys():
                alt_param = self.paramater_alternate_dict[param]
                # If the new version of the parameter is not in the paramter dict then us the value in the deprectaed parameter
                if alt_param not in parameter_dict.keys():
                    param = alt_param
                else:
                    # If the new version of the parameter is in the dict then ignore the current deprecated parameter
                    ignore_deprecated = True

            
            if ignore_deprecated == False:
                setattr(self, param, value)

        self.switch_config = SwitchConfig(kerf = self.kerf, switch_type = self.switch_type, stabilizer_type = self.stabilizer_type, custom_shape = self.custom_shape, custum_shape_points = self.custum_shape_points, custom_shape_path = self.custom_shape_path)

        self.update_calculated_attributes()

        self.validate_parameters()
    
    
    def set_parameter_dict(self, parameter_dict):
        self.parameter_dict = parameter_dict
        self.build_attr_from_dict(self.parameter_dict)
    
    
    def get_param(self, paramaeter_name):

        if self.parameter_dict is not None and paramaeter_name in self.parameter_dict.keys():
            return self.parameter_dict[paramaeter_name]
        elif paramaeter_name in self.default_parameter_dict.keys():
            return self.default_parameter_dict[paramaeter_name]
        else:
            raise ValueError('No paramter exists with name %s' % (paramaeter_name))



    def validate_parameters(self):
        parameter_error = False
        error_message = ''
        if self.screw_edge_inset < self.case_wall_thickness + self.screw_hole_body_radius:
            parameter_error = True
            error_message += 'Screw Edge Inset %f must be greater than case_wall_thickness: %f + screw_hole_body_radius: %f = %f\n' % (self.screw_edge_inset, self.case_wall_thickness, self.screw_hole_body_radius, self.case_wall_thickness + self.screw_hole_body_radius)
        

        if parameter_error == True:
            print(error_message)
            exit(1)