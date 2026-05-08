#include "tensor.h"
#include <opencv2/opencv.hpp>
#include <utility>
#include "../log.h"
#include "sample.h"
/*
rows = h
cols = w
*/
namespace DeepLr::Neural {
	Tensor3D::Tensor3D():c(1),w(NEURAL_W),h(NEURAL_H),data(1 * NEURAL_W * NEURAL_H,0.0f) {}
	Tensor3D::Tensor3D(int32_t c, int32_t w, int32_t h){
		this->c = c;
		this->w = w;
		this->h = h;
		this->data = std::vector(c * w * h, 0.0f);
	}
	Tensor3D::Tensor3D(const Tensor3D& tensor3D) {
		this->c = tensor3D.c;
		this->w = tensor3D.w;
		this->h = tensor3D.h;
		this->data = tensor3D.data;
	}
	Tensor3D::Tensor3D(Tensor3D&& tensor3D) {
		this->c = tensor3D.c;
		this->w = tensor3D.w;
		this->h = tensor3D.h;
		this->data = std::move(tensor3D.data);
	}

	Tensor3D& Tensor3D::operator=(const Tensor3D& tensor3D) {
		if (this == &tensor3D) {
			return *this;
		}
		this->c = tensor3D.c;
		this->w = tensor3D.w;
		this->h = tensor3D.h;
		this->data = tensor3D.data;
		return *this;
	}

	Tensor3D& Tensor3D::operator=(Tensor3D&& tensor3D) noexcept {
		if (this == &tensor3D) {
			return *this;
		}
		this->c = tensor3D.c;
		this->w = tensor3D.w;
		this->h = tensor3D.h;
		this->data = std::move(tensor3D.data);
		return *this;
	}

	Tensor3D Tensor3D::Load(const std::string& path) {
		cv::Mat img = cv::imread(path, cv::IMREAD_GRAYSCALE);
		Tensor3D tensor3D;
		if (img.empty()) {
			Log::Debug("Failed to read image:" + path);
			return tensor3D;
		}
		if (img.cols != NEURAL_W || img.rows != NEURAL_H) {
			Log::Debug(std::format("current size:{}:{},Activate forced scaling.", img.cols, img.rows));
			cv::resize(img, img, cv::Size(128, 128), 0, 0, cv::INTER_LINEAR);
		}
		for (int32_t y = 0; y < NEURAL_H; ++y) {
			const uchar* row = img.ptr<uchar>(y);
			for (int32_t x = 0; x < 128; ++x) {
				tensor3D.At(0, y, x) = row[x] / 255.0f;
			}
		}
		return tensor3D;
		
	}
}