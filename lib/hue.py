class Hue:

    def from_DT_Switch_to_off_on(x):
        # 0 - 1 translated to off / on
        if str(x) == "0":
            return "False"
        else:
            return "True"

    def from_off_on_to_DT_Switch(x):
        # off - on translated to 0 - 1
        if x == "False":
            return 0
        else:
            return 1

