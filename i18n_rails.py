import re
from base_command import BaseCommand
from yaml import Yaml

# 1. Toggle highlight
class I18nRailsToggleCommand(BaseCommand):
    def work(self):
        global i18n_rails_keys_enabled

        # Default value
        if not 'i18n_rails_keys_enabled' in globals():
            i18n_rails_keys_enabled = True 
        
        self.setup_regions()

        if i18n_rails_keys_enabled:
            self.highlight_keys()
        else:
           self.clear_highlighted_keys()

        i18n_rails_keys_enabled = not i18n_rails_keys_enabled

    def setup_regions(self):
        self.regions = {
            'valid'  : ([], self.settings.get("valid_color_scope",   "comment")),
            'partial': ([], self.settings.get("partial_color_scope", "string")),
            'invalid': ([], self.settings.get("invalid_color_scope", "invalid"))
        }

    def highlight_keys(self):
        self.yaml = Yaml(self.locales_path)

        method_call_regions = self.view.find_all('\s*(?:I18n\.)?t(?:\(|\s+)["\'](\.?[\w\.]+)["\']\)?\s*')

        for method_call_region in method_call_regions:
            key = self.find_key_in_method_call(method_call_region)
            
            if self.add_yml_file_paths_by(key):
                self.add_to_regions(method_call_region, key)

        self.paint_highlighted_keys()

    def find_key_in_method_call(self, method_call_region):
        return re.search('["\'](\.?[\w\.]+)["\']', self.view.substr(method_call_region)).group(1)

    def add_to_regions(self, region, key):
        locales_len = self.locales_path.locales_len()
        translations_count = self.yaml.value_count(key)

        if translations_count == locales_len:
            self.regions['valid'][0].append(region)
        elif translations_count > 0:
            self.regions['partial'][0].append(region)
        else:
            self.regions['invalid'][0].append(region)

    def paint_highlighted_keys(self):
        for region_name, regions_tuple in self.regions.items():
            self.add_regions(region_name, regions_tuple[0], regions_tuple[1])

    def clear_highlighted_keys(self):
        for region_name in self.regions.keys():
            self.erase_regions(region_name)

# 2. Add keys
class I18nRailsCommand(BaseCommand):
    def work(self):
        # Object to read and parse a yaml file
        self.yaml = Yaml(self.locales_path)

        self.for_each_selected_text(self.store_selected_text)

    def store_selected_text(self, selected_text):
        self.selected_text = selected_text
        self.write_and_show_input()

    def write_and_show_input(self, user_text = None):
        # Write the files keeping in mind the presence (or lack of) a dot to place the keys in the yml
        if user_text:
            self.write_text(user_text)

        locale = self.locales_path.process()
        if locale:
            existing_value = self.existing_value_from_yaml()
            self.show_input_panel(locale, existing_value, self.write_and_show_input, None, self.write_and_show_input)

    def write_text(self, text):
        self.yaml.write_text(text)
        self.display_message("{0} created!".format(self.selected_text))

    def key_parent_notice(self, parent):
        return "The key is the parent of: {keys}".format(self.joined_keys(parent)) if not parent is None else ""

# 3. Go to file
class I18nRailsGoToFileCommand(BaseCommand):
    def work(self):
        self.text_to_display = []
        self.paths = []

        self.yaml = Yaml(self.locales_path)

        self.for_each_selected_text(self.show_yaml_files_in_quick_panel)

    def show_yaml_files_in_quick_panel(self, selected_text):
        self.selected_text = selected_text

        self.locales_path.for_each_process(self.fill_paths_and_text)

        self.show_quick_panel(self.text_to_display, self.open_file, self.preview_file)

    def fill_paths_and_text(self, locale):
        existing_value = self.existing_value_from_yaml()

        if existing_value:
            self.text_to_display.append( locale + ": " + existing_value )
        else:
            self.text_to_display.append( locale )
            
        self.paths.append(self.locales_path.yaml())

    def key_parent_notice(self, parent):
        return "Parent of {keys}".format(self.joined_keys(parent)) if not parent is None else ""
