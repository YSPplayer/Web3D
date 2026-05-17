#include "conv2d.h"
#include "../log.h"
#include <format>
namespace DeepLr::Neural {
	Conv2D::Conv2D(int32_t ksize,int32_t shape):Layer(), ksize(ksize), shape(shape){
		ntype = NeuralType::Conv2D;
		kernels.resize(ksize);
		dkernels.resize(ksize);
		for (int32_t i = 0; i < ksize; ++i) {
			kernels[i] = Tensor3D(shape,3,3);
			kernels[i].HeUniform(shape * 3 * 3);
			dkernels[i] = Tensor3D(shape, 3, 3);
		}
		bias = Tensor3D(ksize,1,1);
		dbias = Tensor3D(ksize, 1, 1);
	}

	Tensor3D Conv2D::Forward(const Tensor3D& input, const std::array<int32_t, 4>& target) {
		oldx = input;
		if (input.Channel() != shape) {
			throw std::invalid_argument("Conv2D input channel does not match kernel input channel");
		}
		Tensor3D tensor3D(ksize, input.Width(), input.Height());
		// y = conv2D(w,x)
		for (int32_t i = 0; i < ksize; ++i) {
			const Tensor3D& kernel = kernels[i];
			for (int32_t y = 0; y < input.Height(); ++y) {
				for (int32_t x = 0; x < input.Width(); ++x) {
					float sum = bias.At(i, 0, 0);
					for (int32_t j = 0; j < shape; ++j) {
						for (int32_t ky = 0; ky < 3; ++ky) {
							for (int32_t kx = 0; kx < 3; ++kx) {
								int32_t inputY = y + ky - 1;
								int32_t inputX = x + kx - 1;
								sum += kernel.Get(j, ky, kx) * input.Get(j, inputY, inputX);
							}
						}
					}
					tensor3D.At(i, y, x) = sum;
				}
			}
		
		}
		return tensor3D;
	}
	Tensor3D Conv2D::Backward(const Tensor3D& output, const std::array<int32_t, 4>& target) {
		Tensor3D tensor3D(shape, output.Width(), output.Height());
		//db = dy * 1
		for (int32_t i = 0; i < output.Channel(); ++i) {
			float sum = 0.0f;
			for (int32_t y = 0; y < output.Height(); ++y) {
				for (int32_t x = 0; x < output.Width(); ++x) {
					sum += output.At(i,y, x);
				}
			}
			dbias.At(i,0,0) += sum;
		}
		//dx = conv2D(dY, rot180(W))
		for (int32_t ic = 0; ic < shape; ++ic) {
			for (int32_t y = 0; y < output.Height(); ++y) {
				for (int32_t x = 0; x < output.Width(); ++x) {
					float sum = 0.0f;
					for (int32_t oc = 0; oc < ksize; ++oc) {
						const Tensor3D& kernel = kernels[oc];
						for (int32_t ky = 0; ky < 3; ++ky) {
							for (int32_t kx = 0; kx < 3; ++kx) {
								int32_t dy = y + ky - 1;
								int32_t dx = x + kx - 1;
								sum += output.Get(oc, dy, dx) *
									kernel.Get(ic, 2 - ky, 2 - kx);
							}
						}
					}
					tensor3D.At(ic, y, x) = sum;
				}
			}
		}
		//dw = conv2D(X, dY)
		for (int32_t oc = 0; oc < ksize; ++oc) {
			for (int32_t ic = 0; ic < shape; ++ic) {
				for (int32_t ky = 0; ky < 3; ++ky) {
					for (int32_t kx = 0; kx < 3; ++kx) {
						float sum = 0.0f;
						for (int32_t y = 0; y < output.Height(); ++y) {
							for (int32_t x = 0; x < output.Width(); ++x) {
								int32_t inputY = y + ky - 1;
								int32_t inputX = x + kx - 1;

								sum += output.Get(oc, y, x) *
									oldx.Get(ic, inputY, inputX);
							}
						}
						dkernels[oc].At(ic, ky, kx) += sum;
					}
				}
			}
		}
		return tensor3D;
	}
	void Conv2D::Update(float lr, int32_t batchSize) {
		float oldK0 = (!kernels.empty() && kernels[0].Count() > 0) ? kernels[0].At(0) : 0.0f;
		float oldB0 = bias.Count() > 0 ? bias.At(0) : 0.0f;
		float dkAbs = Tensor3D::SumAbs(dkernels);
		float dbAbs = dbias.SumAbs();
		float scale = lr / (float)batchSize;
		for (int32_t i = 0; i < ksize; ++i) {
			kernels[i] = kernels[i] - dkernels[i] * scale;
			dkernels[i] = Tensor3D(shape, 3, 3);
		}
		bias = bias - dbias * scale;
		if (batchSize <= 8) {
			float newK0 = (!kernels.empty() && kernels[0].Count() > 0) ? kernels[0].At(0) : 0.0f;
			float newB0 = bias.Count() > 0 ? bias.At(0) : 0.0f;
			Log::Debug(std::format(
				"debug Conv2D update inC={},outC={},batch={},dkAbs={},dbAbs={},k0Before={},k0After={},b0Before={},b0After={}",
				shape, ksize, batchSize, dkAbs, dbAbs, oldK0, newK0, oldB0, newB0));
		}
		dbias = Tensor3D(ksize, 1, 1);
	}
}
