#include "conv2d.h"
namespace DeepLr::Neural {
	Conv2D::Conv2D(){
		kernels.resize(8);
		for (int32_t i = 0; i < 8; ++i) {
			kernels[i] = Kernel(3,1,1);
		}
	}

	Tensor3D Conv2D::Forward(const Tensor3D& input) {
		Tensor3D tensor3D(kernels.size(), NEURAL_W, NEURAL_H);
		for (int32_t i = 0; i < kernels.size(); ++i) {
			const Kernel& kernel = kernels[i];
			const float** data = kernel.data;
			for (int32_t y = 0; y < input.Height(); ++y) {
				for (int32_t x = 0; x < input.Width(); ++x) {
					float value1 = input.Get(0, y - 1, x - 1);
					float value2 = input.Get(0, y - 1, x);
					float value3 = input.Get(0, y - 1, x + 1);
					float value4 = input.Get(0, y, x - 1);
					float value5 = input.Get(0, y, x);
					float value6 = input.Get(0, y, x + 1);
					float value7 = input.Get(0, y + 1, x - 1);
					float value8 = input.Get(0, y + 1, x);
					float value9 = input.Get(0, y + 1, x + 1);
					float result = data[0][0] * value1 + data[0][1] * value2
						+ data[0][2] * value3 + data[1][0] * value4 + data[1][1]
						* value5 + data[1][2] * value6 + data[2][0] * value7 + data[2][1] * value8
						+ data[2][2] * value9;
					tensor3D.At(i,y,x) = result;
				}
			}
		}
		return tensor3D;
	}
}