class initial_fields():
    def __init__(self):
        self.index = 0
        self.max_index = None
        self.current_file_path = None
        self.global_time = 0
        self.time_step=0
        self.bin_factor = 6
        self.colormap_scheme = "viridis"
        self.threshold = -20
        self.current_x_range = [0,0]
        self.total_time_len = 0