#include "conv2d.h"
#include "../log.h"
#include <format>
namespace DeepLr::Neural {
	Conv2D::Conv2D():Layer() {
		ntype = NeuralType::Conv2D;
	}
	void Conv2D::SetShape(const TensorShape& lastshape, const TensorShape& shape) {
		Layer::SetShape(lastshape, shape);
		kernels.resize(shape.c);
		dkernels.resize(shape.c);
		for (int32_t i = 0; i < shape.c; ++i) {
			kernels[i] = Tensor3D(lastshape.c,3,3);
			kernels[i].HeUniform(lastshape.c * 3 * 3);
			dkernels[i] = Tensor3D(lastshape.c, 3, 3);
		}
		bias = Tensor3D(shape.c,1,1);
		dbias = Tensor3D(shape.c, 1, 1);
	}

	Tensor3D Conv2D::Forward(const Tensor3D& input) {
		oldx = input;
		if (input.Channel() != lastshape.c) {
			throw std::invalid_argument("Conv2D input channel does not match kernel input channel");
		}
		Tensor3D tensor3D(shape.c, shape.w, shape.h);
		// y = conv2D(w,x)
		for (int32_t i = 0; i < shape.c; ++i) {
			const Tensor3D& kernel = kernels[i];
			for (int32_t y = 0; y < tensor3D.Height(); ++y) {
				for (int32_t x = 0; x < tensor3D.Width(); ++x) {
					float sum = bias.At(i, 0, 0);
					for (int32_t j = 0; j < lastshape.c; ++j) {
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
		Tensor3D tensor3D(lastshape.c, lastshape.w, lastshape.h);
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
		for (int32_t ic = 0; ic < lastshape.c; ++ic) {
			for (int32_t y = 0; y < output.Height(); ++y) {
				for (int32_t x = 0; x < output.Width(); ++x) {
					float sum = 0.0f;
					for (int32_t oc = 0; oc < shape.c; ++oc) {
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
		for (int32_t oc = 0; oc < shape.c; ++oc) {
			for (int32_t ic = 0; ic < lastshape.c; ++ic) {
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
		for (int32_t i = 0; i < shape.c; ++i) {
			kernels[i] = kernels[i] - dkernels[i] * scale;
			dkernels[i] = Tensor3D(lastshape.c, 3, 3);
		}
		bias = bias - dbias * scale;
		if (batchSize <= 8) {
			float newK0 = (!kernels.empty() && kernels[0].Count() > 0) ? kernels[0].At(0) : 0.0f;
			float newB0 = bias.Count() > 0 ? bias.At(0) : 0.0f;
			Log::Debug(std::format(
				"debug Conv2D update inC={},outC={},batch={},dkAbs={},dbAbs={},k0Before={},k0After={},b0Before={},b0After={}",
				lastshape.c, shape.c, batchSize, dkAbs, dbAbs, oldK0, newK0, oldB0, newB0));
		}
		dbias = Tensor3D(shape.c, 1, 1);
	}
	void Conv2D::SetKernels(const std::vector<Tensor3D>& kernels) {
		this->kernels = kernels;
	}
	void Conv2D::SetBias(const Tensor3D& bias) {
		this->bias = bias;
	}
}
