from PIL import Image
import time
import epd10in2g

# Initialize display
epd = epd10in2g.EPD()
epd.init()

# Load images
image1 = Image.open("1.png")
image2 = Image.open("2.png")
image3 = Image.open("3.png")

cycles = 20  # number of cycles to run
count = 0

try:
    while count < cycles:
        # Display first image
        epd.display(epd.getbuffer(image1))
        time.sleep(10)

        # Display second image
        epd.display(epd.getbuffer(image2))
        time.sleep(10)

        # Display third image
        epd.display(epd.getbuffer(image3))
        time.sleep(10)
        count += 1  # one full cycle counts as 1

except KeyboardInterrupt:
    print("Interrupted by user")

finally:
    # Clear the screen to reduce ghosting, then sleep
    epd.Clear()
    epd.sleep()
    print("Done after 20 cycles.")