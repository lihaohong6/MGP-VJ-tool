import dataclasses


@dataclasses.dataclass
class Color:
    red: int
    green: int
    blue: int

    def __getitem__(self, item: int):
        if item == 0:
            return self.red
        if item == 1:
            return self.green
        if item == 2:
            return self.blue
        raise IndexError("A color only has length 3.")

    def perceived_lightness(self) -> int:
        vR = self.red / 255
        vG = self.green / 255
        vB = self.blue / 255

        def rgb_to_linear(color_channel):
            if color_channel <= 0.04045:
                return color_channel / 12.92
            else:
                return pow(((color_channel + 0.055) / 1.055), 2.4)

        Y = (0.2126 * rgb_to_linear(vR) +
             0.7152 * rgb_to_linear(vG) +
             0.0722 * rgb_to_linear(vB))
        if Y <= (216 / 24389):
            ans = Y * (24389 / 27)
        else:
            ans = pow(Y, (1 / 3)) * 116 - 16
        return round(ans)

    def to_hex(self) -> str:
        return '#%02x%02x%02x' % (self.red, self.green, self.blue)


def text_color(c: Color) -> Color:
    white = Color(255, 255, 255)
    num = c.perceived_lightness()
    if num > white.perceived_lightness() / 2:
        return Color(0, 0, 0)
    return white


@dataclasses.dataclass
class ColorScheme:
    text: Color
    background: Color = None