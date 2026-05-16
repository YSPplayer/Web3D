#include "conv2d.h"
namespace DeepLr::Neural {
	Conv2D::Conv2D(int32_t ksize,int32_t shape):Layer(), ksize(ksize), shape(shape){
		ntype = NeuralType::Conv2D;
		kernels.resize(ksize * shape);
		for (int32_t i = 0; i < ksize * shape; ++i) {
			kernels[i] = Kernel(3,1,1);
		}
		bias = Tensor3D(ksize,1,1);
	}

	Tensor3D Conv2D::Forward(const Tensor3D& input, const std::array<int32_t, 4>& target) {
		oldx = input;
		Tensor3D tensor3D(ksize, input.Width(), input.Height());
		for (int32_t i = 0; i < ksize; ++i) {
			for (int32_t y = 0; y < input.Height(); ++y) {
				for (int32_t x = 0; x < input.Width(); ++x) {
					float sum = bias.At(i, 0, 0);
					for (int32_t j = 0; j < input.Channel(); ++j) {
						const Kernel& kernel = kernels[i * input.Channel() + j];
						const float** data = kernel.data;

						float value1 = input.Get(j, y - 1, x - 1);
						float value2 = input.Get(j, y - 1, x);
						float value3 = input.Get(j, y - 1, x + 1);
						float value4 = input.Get(j, y, x - 1);
						float value5 = input.Get(j, y, x);
						float value6 = input.Get(j, y, x + 1);
						float value7 = input.Get(j, y + 1, x - 1);
						float value8 = input.Get(j, y + 1, x);
						float value9 = input.Get(j, y + 1, x + 1);
						sum += data[0][0] * value1 + data[0][1] * value2
							+ data[0][2] * value3 + data[1][0] * value4 + data[1][1]
							* value5 + data[1][2] * value6 + data[2][0] * value7 + data[2][1] * value8
							+ data[2][2] * value9;
					}
					tensor3D.At(i, y, x) = sum;
				}
			}
		
		}
		return tensor3D;
	}
	Tensor3D Conv2D::Backward(const Tensor3D& output, const std::array<int32_t, 4>& target) {
		Tensor3D tensor3D(1, output.Width(), output.Height());
		dbias = bias;
		for (int32_t i = 0; i < tensor3D.Channel(); ++i) {
			float sum = 0.0f;
			for (int32_t y = 0; y < output.Height(); ++y) {
				for (int32_t x = 0; x < output.Width(); ++x) {
					sum += output.At(i,y, x);
				}
			}
			dbias.At(i,1,1) = sum;
		}

		for (int32_t i = 0; i < tensor3D.Channel(); ++i) {
			Kernel dkernel(kernels[i]);
			dkernel.Rot180();
			const float** data = dkernel.data;
			for (int32_t y = 0; y < output.Height(); ++y) {
				for (int32_t x = 0; x < output.Width(); ++x) {
					float value1 = output.Get(i, y - 1, x - 1);
					float value2 = output.Get(i, y - 1, x);
					float value3 = output.Get(i, y - 1, x + 1);
					float value4 = output.Get(i, y, x - 1);
					float value5 = output.Get(i, y, x);
					float value6 = output.Get(i, y, x + 1);
					float value7 = output.Get(i, y + 1, x - 1);
					float value8 = output.Get(i, y + 1, x);
					float value9 = output.Get(i, y + 1, x + 1);
					float result = data[0][0] * value1 + data[0][1] * value2
						+ data[0][2] * value3 + data[1][0] * value4 + data[1][1]
						* value5 + data[1][2] * value6 + data[2][0] * value7 + data[2][1] * value8
						+ data[2][2] * value9;
					tensor3D.At(i, y, x) = result;
				}
			}
		}
		return tensor3D;
	}
}