#include "maxpool.h"
namespace DeepLr::Neural {
	MaxPool::MaxPool():Layer() {
		kernel = Kernel(2,0,2);
	}
	Tensor3D MaxPool::Forward(const Tensor3D& input) {
		Tensor3D tensor3D(input.Channel(), input.Width() / 2, input.Height() / 2);
		int32_t c = input.Channel();
		int32_t h = input.Height();
		int32_t w = input.Width();
		int32_t index = 0;
		for (int32_t i = 0; i < c; ++i) {
			for (int32_t y = 0; y < h; y+=2) {
				for (int32_t x = 0; x < w; x+=2) {
					float value1 = input.Get(i,y,x);
					float value2 = input.Get(i, y, x + 1);
					float value3 = input.Get(i, y + 1, x);
					float value4 = input.Get(i, y + 1, x + 1);
					float maxvalue = std::max({ value1, value2, value3, value4 });
					tensor3D.At(index++) = maxvalue;
				}
			}
		}
		return tensor3D;
	}
}